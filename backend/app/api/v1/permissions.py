from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_admin
from app.models.user import User
from app.models.permission import Permission
from app.schemas.permission import PermissionResponse, PermissionsBulkUpdate
from app.utils.constants import PERMISSION_FEATURES

router = APIRouter(prefix="/permissions", tags=["Permissions"])


@router.get("/features")
def get_features(_: User = Depends(require_admin)):
    return {"features": PERMISSION_FEATURES}


@router.get("/users/{user_id}", response_model=list[PermissionResponse])
def get_user_permissions(
    user_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    return db.query(Permission).filter(Permission.user_id == user_id).all()


@router.put("/users/{user_id}")
def update_user_permissions(
    user_id: int,
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

    db.commit()
    return {"message": "Permisos actualizados"}
