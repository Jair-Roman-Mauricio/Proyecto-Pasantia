import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, require_admin
from app.models.user import User
from app.models.permission import Permission
from app.schemas.permission import PermissionResponse, PermissionsBulkUpdate
from app.utils.constants import PERMISSION_FEATURES
from app.utils.db_helpers import safe_commit

router = APIRouter(prefix="/permissions", tags=["Permissions"])


@router.get(
    "/me",
    response_model=list[PermissionResponse],
    summary="Mis permisos",
    description="Retorna la lista de permisos del usuario autenticado. El frontend lo usa al iniciar sesión para mostrar solo las opciones habilitadas. Cualquier usuario autenticado puede llamar este endpoint.",
    response_description="Lista de permisos del usuario actual",
    responses={401: {"description": "No autenticado"}},
)
def get_my_permissions(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return db.query(Permission).filter(Permission.user_id == user.id).all()


@router.get(
    "/features",
    summary="Listar features disponibles",
    description="Retorna la lista de todas las features (permisos) que pueden asignarse a usuarios OPERSAC: `view_stations`, `view_circuits`, `send_requests`, `add_observations`, `view_reports`. Solo admin.",
    response_description="Objeto con array `features` de strings",
    responses={401: {"description": "No autenticado"}, 403: {"description": "Se requiere rol admin"}},
)
def get_features(_: User = Depends(require_admin)):
    return {"features": PERMISSION_FEATURES}


@router.get(
    "/users/{user_id}",
    response_model=list[PermissionResponse],
    summary="Permisos de un usuario",
    description="Retorna la lista de permisos de un usuario OPERSAC específico. Solo admin.",
    response_description="Lista de permisos del usuario indicado",
    responses={401: {"description": "No autenticado"}, 403: {"description": "Se requiere rol admin"}},
)
def get_user_permissions(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    return db.query(Permission).filter(Permission.user_id == user_id).all()


@router.put(
    "/users/{user_id}",
    summary="Actualizar permisos de un usuario",
    description="""Actualiza los permisos de un usuario OPERSAC en bloque. Solo admin.\n\nEnviar un array con los permisos a modificar:\n```json\n{\n  "permissions": [\n    {"feature_key": "view_stations", "is_allowed": true},\n    {"feature_key": "send_requests", "is_allowed": false}\n  ]\n}\n```\nSolo los permisos incluidos serán modificados.""",
    response_description="Mensaje de confirmación",
    responses={401: {"description": "No autenticado"}, 403: {"description": "Se requiere rol admin"}, 404: {"description": "Usuario no encontrado"}},
)
def update_user_permissions(
    user_id: uuid.UUID,
    data: PermissionsBulkUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    for perm_update in data.permissions:
        perm = (
            db.query(Permission)
            .filter(
                Permission.user_id == user_id,
                Permission.feature_key == perm_update.feature_key,
            )
            .first()
        )
        if perm:
            perm.is_allowed = perm_update.is_allowed
        else:
            perm = Permission(
                user_id=user_id,
                feature_key=perm_update.feature_key,
                is_allowed=perm_update.is_allowed,
            )
            db.add(perm)

    safe_commit(db)
    return {"message": "Permisos actualizados"}
