from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import io

from app.database import get_db
from app.dependencies import require_admin
from app.models.user import User
from app.models.audit_log import AuditLog
from app.schemas.audit import AuditLogResponse, AuditFlagUpdate
from app.services.audit_service import AuditService

router = APIRouter(prefix="/audit", tags=["Audit"])


@router.get("", response_model=list[AuditLogResponse])
def get_audit_logs(
    entity_type: str | None = None,
    entity_id: int | None = None,
    user_id: int | None = None,
    is_flagged: bool | None = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    query = db.query(AuditLog)
    if entity_type:
        query = query.filter(AuditLog.entity_type == entity_type)
    if entity_id:
        query = query.filter(AuditLog.entity_id == entity_id)
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    if is_flagged is not None:
        query = query.filter(AuditLog.is_flagged == is_flagged)

    return (
        query.order_by(AuditLog.action_date.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )


@router.put("/{log_id}/flag", response_model=AuditLogResponse)
def flag_audit_log(
    log_id: int,
    data: AuditFlagUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    service = AuditService(db)
    log = service.flag_log(log_id, data.is_flagged, data.flag_reason)
    if not log:
        raise HTTPException(status_code=404, detail="Registro de auditoria no encontrado")
    return log


@router.get("/export/excel")
def export_audit_excel(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    from openpyxl import Workbook

    logs = db.query(AuditLog).order_by(AuditLog.action_date.desc()).all()

    wb = Workbook()
    ws = wb.active
    ws.title = "Auditoria"
    ws.append(["ID", "Usuario ID", "Rol", "Nombre", "Fecha", "Accion", "Entidad", "ID Entidad", "Destacado"])

    for log in logs:
        ws.append([
            log.id,
            log.user_id,
            log.user_role,
            log.user_name,
            log.action_date.strftime("%Y-%m-%d %H:%M:%S") if log.action_date else "",
            log.action,
            log.entity_type,
            log.entity_id,
            "Si" if log.is_flagged else "No",
        ])

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=auditoria.xlsx"},
    )
