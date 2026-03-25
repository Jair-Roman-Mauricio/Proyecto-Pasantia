import uuid

from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import get_current_user, require_admin
from app.subest_client import get_subest_client
from app.schemas.permission import PermissionResponse, PermissionsBulkUpdate
from app.utils.constants import PERMISSION_FEATURES

router = APIRouter(prefix="/permissions", tags=["Permissions"])


@router.get("/me", response_model=list[PermissionResponse])
def get_my_permissions(user=Depends(get_current_user)):
    client = get_subest_client()
    result = client.table("permissions").select("*").eq("user_id", str(user.id)).execute()
    return result.data


@router.get("/features")
def get_features(_=Depends(require_admin)):
    return {"features": PERMISSION_FEATURES}


@router.get("/users/{user_id}", response_model=list[PermissionResponse])
def get_user_permissions(user_id: uuid.UUID, _=Depends(require_admin)):
    client = get_subest_client()
    result = client.table("permissions").select("*").eq("user_id", str(user_id)).execute()
    return result.data


@router.put("/users/{user_id}")
def update_user_permissions(user_id: uuid.UUID, data: PermissionsBulkUpdate, _=Depends(require_admin)):
    client = get_subest_client()
    user_result = client.table("users").select("id").eq("id", str(user_id)).execute()
    if not user_result.data:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    for perm_update in data.permissions:
        existing = client.table("permissions").select("id").eq("user_id", str(user_id)).eq("feature_key", perm_update.feature_key).execute()
        if existing.data:
            client.table("permissions").update({"is_allowed": perm_update.is_allowed}).eq("id", existing.data[0]["id"]).execute()
        else:
            client.table("permissions").insert({
                "user_id": str(user_id),
                "feature_key": perm_update.feature_key,
                "is_allowed": perm_update.is_allowed,
            }).execute()

    return {"message": "Permisos actualizados"}
