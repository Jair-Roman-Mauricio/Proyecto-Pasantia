from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
import io

from app.dependencies import require_admin
from app.subest_client import get_subest_client
from app.schemas.audit import AuditLogResponse, AuditFlagUpdate
from app.services.audit_service import AuditService

router = APIRouter(prefix="/audit", tags=["Audit"])


@router.get("", response_model=list[AuditLogResponse])
def get_audit_logs(
    entity_type: str | None = None,
    entity_id: str | None = None,
    user_id: str | None = None,
    action: str | None = None,
    is_flagged: bool | None = None,
    limit: int = 100,
    offset: int = 0,
    _=Depends(require_admin),
):
    client = get_subest_client()
    query = client.table("audit_logs").select("*")
    if entity_type:
        query = query.eq("entity_type", entity_type)
    if entity_id:
        query = query.eq("entity_id", str(entity_id))
    if user_id:
        query = query.eq("user_id", str(user_id))
    if action:
        query = query.ilike("action", f"%{action}%")
    if is_flagged is not None:
        query = query.eq("is_flagged", is_flagged)

    result = query.order("action_date", desc=True).range(offset, offset + limit - 1).execute()
    return result.data


@router.put("/{log_id}/flag", response_model=AuditLogResponse)
def flag_audit_log(log_id: int, data: AuditFlagUpdate, _=Depends(require_admin)):
    service = AuditService()
    log = service.flag_log(log_id, data.is_flagged, data.flag_reason)
    if not log:
        raise HTTPException(status_code=404, detail="Registro de auditoria no encontrado")
    return log


@router.get("/export/excel")
def export_audit_excel(_=Depends(require_admin)):
    from openpyxl import Workbook
    client = get_subest_client()
    result = client.table("audit_logs").select("*").order("action_date", desc=True).execute()
    logs = result.data

    wb = Workbook()
    ws = wb.active
    ws.title = "Auditoria"
    ws.append(["ID", "Usuario ID", "Rol", "Nombre", "Fecha", "Accion", "Entidad", "ID Entidad", "Destacado"])

    for log in logs:
        ws.append([
            log.get("id"),
            log.get("user_id"),
            log.get("user_role"),
            log.get("user_name"),
            log.get("action_date", "")[:19] if log.get("action_date") else "",
            log.get("action"),
            log.get("entity_type"),
            log.get("entity_id"),
            "Si" if log.get("is_flagged") else "No",
        ])

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=auditoria.xlsx"},
    )
