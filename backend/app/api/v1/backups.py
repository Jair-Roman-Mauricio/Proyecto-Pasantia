import io
import json
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from app.dependencies import require_admin
from app.subest_client import get_subest_client
from app.schemas.backup import BackupCreate, BackupResponse
from app.services.audit_service import AuditService

router = APIRouter(prefix="/backups", tags=["Backups"])

TABLES = ["stations", "bars", "circuits", "sub_circuits", "users",
          "permissions", "observations", "notifications", "requests", "audit_logs"]


def _collect_backup_data(client, includes_audit: bool) -> dict:
    data = {}
    for table in TABLES:
        if table == "audit_logs" and not includes_audit:
            continue
        result = client.table(table).select("*").execute()
        data[table] = result.data
    return data


@router.get("", response_model=list[BackupResponse])
def get_backups(_=Depends(require_admin)):
    client = get_subest_client()
    result = client.table("backups").select("id,created_by,file_name,description,includes_audit,size_bytes,created_at").order("created_at", desc=True).execute()
    return result.data


@router.post("", response_model=BackupResponse, status_code=201)
def create_backup(data: BackupCreate, admin=Depends(require_admin)):
    client = get_subest_client()
    backup_data = _collect_backup_data(client, data.includes_audit)
    backup_json = json.dumps(backup_data, default=str)
    size_bytes = len(backup_json.encode("utf-8"))
    file_name = f"backup_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"

    result = client.table("backups").insert({
        "created_by": str(admin.id),
        "file_name": file_name,
        "description": data.description,
        "backup_data": backup_data,
        "includes_audit": data.includes_audit,
        "size_bytes": size_bytes,
    }).execute()

    if not result.data:
        raise HTTPException(status_code=500, detail="Error al crear backup")

    AuditService().log(user=admin, action="CREATE_BACKUP", entity_type="backup",
                       entity_id=result.data[0]["id"], details={"file_name": file_name})
    return result.data[0]


@router.get("/{backup_id}/download")
def download_backup(backup_id: int, _=Depends(require_admin)):
    client = get_subest_client()
    result = client.table("backups").select("*").eq("id", backup_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Backup no encontrado")
    backup = result.data[0]
    content = json.dumps(backup["backup_data"], indent=2, default=str).encode("utf-8")
    return StreamingResponse(
        io.BytesIO(content),
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename={backup['file_name']}"},
    )


@router.delete("/{backup_id}")
def delete_backup(backup_id: int, admin=Depends(require_admin)):
    client = get_subest_client()
    result = client.table("backups").select("id").eq("id", backup_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Backup no encontrado")
    client.table("backups").delete().eq("id", backup_id).execute()
    AuditService().log(user=admin, action="DELETE_BACKUP", entity_type="backup", entity_id=backup_id, details={})
    return {"message": "Backup eliminado"}
