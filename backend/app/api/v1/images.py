from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse, Response

from app.dependencies import get_current_user, require_admin
from app.services.image_service import ImageService
from app.services.audit_service import AuditService

router = APIRouter(prefix="/images", tags=["Images"])
image_service = ImageService()


@router.get(
    "/{entity_type}/{entity_id}",
    summary="Obtener imagen de una entidad",
    description="""Retorna la imagen asociada a una entidad del sistema. Cualquier usuario autenticado puede ver imágenes.\n\n**Tipos de entidad válidos:** `station`, `bar`, `circuit`, `sub_circuit`\n\nEl parámetro opcional `sub_id` permite obtener imágenes de sub-entidades (p. ej., sub-circuito específico dentro de un circuito).""",
    response_description="Archivo de imagen (PNG, JPG, etc.)",
    responses={401: {"description": "No autenticado"}, 404: {"description": "Imagen no encontrada para esta entidad"}},
)
def get_image(
    entity_type: str,
    entity_id: int,
    sub_id: int | None = None,
    _=Depends(get_current_user),
):
    path = image_service.get_image_path(entity_type, entity_id, sub_id)
    if not path:
        # 204 en lugar de 404 para evitar errores en consola del navegador;
        # el frontend interpreta 204 como "sin imagen" y muestra el placeholder.
        return Response(status_code=204)
    return FileResponse(path)


@router.post(
    "/{entity_type}/{entity_id}",
    summary="Subir o reemplazar imagen",
    description="""Sube o reemplaza la imagen de una entidad. Solo admin.\n\nSe debe enviar como `multipart/form-data`:\n- `file` — Archivo de imagen (PNG, JPG, etc.)\n- `justification` — Motivo del cambio (obligatorio, se registra en auditoría)\n- `sub_id` — ID de sub-entidad opcional\n\nSi ya existe una imagen para la entidad, será reemplazada automáticamente.""",
    response_description="Confirmación con la ruta de la imagen guardada",
    responses={400: {"description": "Formato de archivo inválido o entidad no soportada"}, 401: {"description": "No autenticado"}, 403: {"description": "Se requiere rol admin"}},
)
async def upload_image(
    entity_type: str,
    entity_id: int,
    file: UploadFile = File(...),
    justification: str = Form(...),
    sub_id: int | None = Form(None),
    admin=Depends(require_admin),
):
    try:
        path = await image_service.replace_image(entity_type, entity_id, file, sub_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    AuditService().log(
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
