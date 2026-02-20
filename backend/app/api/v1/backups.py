import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text

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

router = APIRouter(prefix="/backups", tags=["Backups"])


def _serialize_model(obj) -> dict:
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


@router.get("", response_model=list[BackupResponse])
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


@router.post("", response_model=BackupResponse)
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
    db.commit()
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


@router.post("/{backup_id}/restore")
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
        # Delete in reverse dependency order (children first)
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

        # Restore in dependency order (parents first)
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

        # Recalculate all station energies
        calculator = EnergyCalculator(db)
        for station in db.query(Station).all():
            calculator.recalculate_station(station.id)

        # Reset sequences so new inserts don't collide with restored IDs
        for tbl in ["stations", "bars", "circuits", "sub_circuits",
                     "observations", "notifications", "requests", "audit_logs"]:
            db.execute(text(
                f"SELECT setval(pg_get_serial_sequence('{tbl}', 'id'), "
                f"COALESCE((SELECT MAX(id) FROM {tbl}), 1))"
            ))
        db.commit()

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al restaurar backup: {str(e)}")

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


@router.delete("/{backup_id}")
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
    db.commit()

    audit = AuditService(db)
    audit.log(
        user=admin,
        action="DELETE_BACKUP",
        entity_type="backup",
        entity_id=backup_id,
        details={"backup_file": file_name},
    )

    return {"message": "Backup eliminado exitosamente"}
