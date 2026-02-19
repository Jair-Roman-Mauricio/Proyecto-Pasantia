from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, require_admin
from app.models.user import User
from app.services.image_service import ImageService
from app.services.audit_service import AuditService

router = APIRouter(prefix="/images", tags=["Images"])
image_service = ImageService()


@router.get("/{entity_type}/{entity_id}")
def get_image(
    entity_type: str,
    entity_id: int,
    sub_id: int | None = None,
    _: User = Depends(get_current_user),
):
    path = image_service.get_image_path(entity_type, entity_id, sub_id)
    if not path:
        raise HTTPException(status_code=404, detail="Imagen no encontrada")
    return FileResponse(path)


@router.post("/{entity_type}/{entity_id}")
async def upload_image(
    entity_type: str,
    entity_id: int,
    file: UploadFile = File(...),
    justification: str = Form(...),
    sub_id: int | None = Form(None),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    try:
        path = await image_service.replace_image(entity_type, entity_id, file, sub_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Log to audit
    audit = AuditService(db)
    audit.log(
        user=admin,
        action="REPLACE_IMAGE",
        entity_type=entity_type,
        entity_id=entity_id,
        details={
            "justification": justification,
            "filename": file.filename,
            "sub_id": sub_id,
        },
    )

    return {"message": "Imagen actualizada exitosamente", "path": str(path)}
