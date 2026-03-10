import glob
import io
import json
import os
import shutil
import subprocess
from datetime import datetime, timezone
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.config import settings
from app.database import get_db
from app.dependencies import require_admin
from app.models.user import User
from app.models.station import Station
from app.models.bar import Bar
from app.models.circuit import Circuit
from app.models.sub_circuit import SubCircuit
from app.models.observation import Observation
from app.models.notification import Notification
from app.models.request import Request
from app.models.audit_log import AuditLog
from app.models.backup import Backup
from app.schemas.backup import BackupCreate, BackupResponse
from app.services.audit_service import AuditService
from app.services.energy_calculator import EnergyCalculator
from app.utils.db_helpers import safe_commit

router = APIRouter(prefix="/backups", tags=["Backups"])


def _serialize_model(obj) -> dict:
    """
    Serializa una instancia de modelo SQLAlchemy a un diccionario JSON-serializable.

    Convierte tipos especiales (datetime, Decimal) a sus representaciones
    estándar en cadena o float para que el resultado sea compatible con json.dumps.

    Retorna un dict con los valores de todas las columnas de la tabla.
    """
    data = {}
    for col in obj.__table__.columns:
        val = getattr(obj, col.name)
        if isinstance(val, datetime):
            val = val.isoformat()
        elif hasattr(val, "isoformat"):
            val = val.isoformat()
        elif hasattr(val, "__float__"):
            val = float(val)
        data[col.name] = val
    return data


@router.get(
    "",
    response_model=list[BackupResponse],
    summary="Listar backups",
    description="Lista todos los backups creados, ordenados del más reciente al más antiguo. Incluye el nombre del creador, tamaño y si contiene logs de auditoría. Solo admin.",
    response_description="Lista de backups disponibles",
    responses={401: {"description": "No autenticado"}, 403: {"description": "Se requiere rol admin"}},
)
def get_backups(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    backups = db.query(Backup).order_by(Backup.created_at.desc()).all()
    result = []
    for b in backups:
        creator = db.query(User).filter(User.id == b.created_by).first()
        result.append(
            BackupResponse(
                id=b.id,
                created_by=b.created_by,
                creator_name=creator.full_name if creator else None,
                file_name=b.file_name,
                description=b.description,
                includes_audit=b.includes_audit,
                size_bytes=b.size_bytes,
                created_at=b.created_at,
            )
        )
    return result


@router.post(
    "",
    response_model=BackupResponse,
    summary="Crear backup",
    description="""Crea un respaldo completo de la base de datos en formato JSON. Solo admin.\n\nEl backup incluye: estaciones, barras, circuitos, sub-circuitos, observaciones, notificaciones y solicitudes.\n\nOpcionalmente puede incluir los logs de auditoría (`includes_audit: true`).\n\nEl backup se guarda en la BD con nombre de archivo `backup_YYYYMMDD_HHMMSS.json`.""",
    response_description="Metadatos del backup creado",
    responses={401: {"description": "No autenticado"}, 403: {"description": "Se requiere rol admin"}},
)
def create_backup(
    data: BackupCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    backup_data = {
        "stations": [_serialize_model(s) for s in db.query(Station).all()],
        "bars": [_serialize_model(b) for b in db.query(Bar).all()],
        "circuits": [_serialize_model(c) for c in db.query(Circuit).all()],
        "sub_circuits": [_serialize_model(sc) for sc in db.query(SubCircuit).all()],
        "observations": [_serialize_model(o) for o in db.query(Observation).all()],
        "notifications": [_serialize_model(n) for n in db.query(Notification).all()],
        "requests": [_serialize_model(r) for r in db.query(Request).all()],
    }

    if data.includes_audit:
        backup_data["audit_logs"] = [
            _serialize_model(a) for a in db.query(AuditLog).all()
        ]

    json_str = json.dumps(backup_data)
    size_bytes = len(json_str.encode("utf-8"))
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    backup = Backup(
        created_by=admin.id,
        file_name=f"backup_{timestamp}.json",
        description=data.description,
        backup_data=backup_data,
        includes_audit=data.includes_audit,
        size_bytes=size_bytes,
    )
    db.add(backup)
    safe_commit(db)
    db.refresh(backup)

    audit = AuditService(db)
    audit.log(
        user=admin,
        action="CREATE_BACKUP",
        entity_type="backup",
        entity_id=backup.id,
        details={"size_bytes": size_bytes},
    )

    return BackupResponse(
        id=backup.id,
        created_by=backup.created_by,
        creator_name=admin.full_name,
        file_name=backup.file_name,
        description=backup.description,
        includes_audit=backup.includes_audit,
        size_bytes=backup.size_bytes,
        created_at=backup.created_at,
    )


@router.post(
    "/{backup_id}/restore",
    summary="Restaurar backup",
    description="""Restaura la base de datos a partir de un backup existente. Solo admin.\n\n**⚠ ADVERTENCIA: Esta acción es DESTRUCTIVA e IRREVERSIBLE.**\n\nEliminará todos los datos actuales (estaciones, barras, circuitos, sub-circuitos, observaciones, notificaciones, solicitudes) y los reemplazará con los del backup.\n\nTras la restauración se recalculan las energías de todas las estaciones y se resetean las secuencias de IDs.""",
    response_description="Mensaje de confirmación",
    responses={401: {"description": "No autenticado"}, 403: {"description": "Se requiere rol admin"}, 404: {"description": "Backup no encontrado"}, 500: {"description": "Error al restaurar — verificar integridad del backup"}},
)
def restore_backup(
    backup_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    backup = db.query(Backup).filter(Backup.id == backup_id).first()
    if not backup:
        raise HTTPException(status_code=404, detail="Backup no encontrado")

    data = backup.backup_data

    try:
        # Eliminar en orden inverso de dependencias (hijos primero)
        db.query(Observation).delete()
        db.query(Notification).delete()
        db.query(Request).delete()
        db.query(SubCircuit).delete()
        db.query(Circuit).delete()
        db.query(Bar).delete()
        db.query(Station).delete()

        if backup.includes_audit and "audit_logs" in data:
            db.query(AuditLog).delete()

        db.flush()

        # Restaurar en orden de dependencias (padres primero)
        for s in data.get("stations", []):
            db.execute(Station.__table__.insert().values(**s))

        for b in data.get("bars", []):
            db.execute(Bar.__table__.insert().values(**b))

        for c in data.get("circuits", []):
            db.execute(Circuit.__table__.insert().values(**c))

        for sc in data.get("sub_circuits", []):
            db.execute(SubCircuit.__table__.insert().values(**sc))

        for o in data.get("observations", []):
            db.execute(Observation.__table__.insert().values(**o))

        for n in data.get("notifications", []):
            db.execute(Notification.__table__.insert().values(**n))

        for r in data.get("requests", []):
            db.execute(Request.__table__.insert().values(**r))

        if backup.includes_audit and "audit_logs" in data:
            for a in data.get("audit_logs", []):
                db.execute(AuditLog.__table__.insert().values(**a))

        db.commit()

        # Recalcular energías de todas las estaciones
        calculator = EnergyCalculator(db)
        for station in db.query(Station).all():
            calculator.recalculate_station(station.id)

        # Reiniciar secuencias para que nuevas inserciones no colisionen con los IDs restaurados
        for tbl in ["stations", "bars", "circuits", "sub_circuits",
                     "observations", "notifications", "requests", "audit_logs"]:
            db.execute(text(
                f"SELECT setval(pg_get_serial_sequence('{tbl}', 'id'), "
                f"COALESCE((SELECT MAX(id) FROM {tbl}), 1))"
            ))
        db.commit()

    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Error al restaurar backup. Verifique la integridad del archivo.")

    # Log restore action
    audit = AuditService(db)
    audit.log(
        user=admin,
        action="RESTORE_BACKUP",
        entity_type="backup",
        entity_id=backup_id,
        details={"backup_file": backup.file_name},
    )

    return {"message": "Backup restaurado exitosamente"}


def _find_pgdump() -> str:
    path = shutil.which("pg_dump")
    if path:
        return path
    # Alternativa para Windows
    candidates = glob.glob(r"C:\Program Files\PostgreSQL\*\bin\pg_dump.exe")
    # Fallback Linux/Ubuntu
    candidates += glob.glob("/usr/lib/postgresql/*/bin/pg_dump")
    candidates += ["/usr/bin/pg_dump"]
    existing = [p for p in sorted(candidates) if os.path.isfile(p)]
    if existing:
        return existing[-1]
    raise HTTPException(
        status_code=503,
        detail="pg_dump no encontrado. Instale postgresql-client o agréguelo al PATH.",
    )


@router.get(
    "/pgdump/download",
    summary="Exportar pg_dump",
    description="Ejecuta pg_dump contra la base de datos actual y descarga un archivo .sql completo. Solo admin.",
    responses={401: {"description": "No autenticado"}, 403: {"description": "Se requiere rol admin"}, 500: {"description": "Error al ejecutar pg_dump"}},
)
def download_pgdump(_: User = Depends(require_admin)):
    parsed = urlparse(settings.DATABASE_URL)
    host = parsed.hostname
    port = str(parsed.port or 5432)
    user = parsed.username
    password = parsed.password or ""
    dbname = parsed.path.lstrip("/")

    env = os.environ.copy()
    env["PGPASSWORD"] = password

    pgdump = _find_pgdump()
    result = subprocess.run(
        [pgdump, "-h", host, "-p", port, "-U", user, "-d", dbname, "--no-owner", "--no-acl"],
        capture_output=True,
        env=env,
    )

    if result.returncode != 0:
        raise HTTPException(status_code=500, detail="Error al ejecutar pg_dump")

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    return StreamingResponse(
        io.BytesIO(result.stdout),
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="pgdump_{timestamp}.sql"'},
    )


@router.get(
    "/{backup_id}/download",
    summary="Descargar backup",
    description="Descarga el archivo JSON del backup. Solo admin.",
    responses={401: {"description": "No autenticado"}, 403: {"description": "Se requiere rol admin"}, 404: {"description": "Backup no encontrado"}},
)
def download_backup(
    backup_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    backup = db.query(Backup).filter(Backup.id == backup_id).first()
    if not backup:
        raise HTTPException(status_code=404, detail="Backup no encontrado")
    content = json.dumps(backup.backup_data, ensure_ascii=False, indent=2).encode("utf-8")
    return StreamingResponse(
        io.BytesIO(content),
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="{backup.file_name}"'},
    )


@router.delete(
    "/{backup_id}",
    summary="Eliminar backup",
    description="Elimina el registro del backup de la base de datos. Solo admin. La acción queda registrada en auditoría.",
    response_description="Mensaje de confirmación",
    responses={401: {"description": "No autenticado"}, 403: {"description": "Se requiere rol admin"}, 404: {"description": "Backup no encontrado"}},
)
def delete_backup(
    backup_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    backup = db.query(Backup).filter(Backup.id == backup_id).first()
    if not backup:
        raise HTTPException(status_code=404, detail="Backup no encontrado")

    file_name = backup.file_name

    db.delete(backup)
    safe_commit(db)

    audit = AuditService(db)
    audit.log(
        user=admin,
        action="DELETE_BACKUP",
        entity_type="backup",
        entity_id=backup_id,
        details={"backup_file": file_name},
    )

    return {"message": "Backup eliminado exitosamente"}
