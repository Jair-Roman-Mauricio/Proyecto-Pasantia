import uuid

from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import require_admin
from app.subest_client import get_subest_client
from app.schemas.user import UserCreate, UserUpdate, UserResponse
from app.services.audit_service import AuditService
from app.utils.constants import PERMISSION_FEATURES

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("", response_model=list[UserResponse])
def get_users(_=Depends(require_admin)):
    client = get_subest_client()
    result = client.table("users").select("id,username,full_name,role,status,created_at,updated_at").order("created_at").execute()
    return result.data


@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: uuid.UUID, _=Depends(require_admin)):
    client = get_subest_client()
    result = client.table("users").select("id,username,full_name,role,status,created_at,updated_at").eq("id", str(user_id)).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return result.data[0]


@router.post("", response_model=UserResponse, status_code=201)
def create_user(data: UserCreate, admin=Depends(require_admin)):
    client = get_subest_client()

    existing = client.table("users").select("id").eq("username", data.username).execute()
    if existing.data:
        raise HTTPException(status_code=400, detail="El nombre de usuario ya existe")

    if data.role not in ("admin", "opersac"):
        raise HTTPException(status_code=400, detail="Rol invalido")

    new_id = str(uuid.uuid4())
    user_payload = {
        "id": new_id,
        "username": data.username,
        "full_name": data.full_name,
        "role": data.role,
        "status": "active",
        "password_hash": data.password,
    }
    if data.email:
        user_payload["email"] = data.email
    if data.phone:
        user_payload["phone"] = data.phone
    result = client.table("users").insert(user_payload).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="Error al crear usuario")
    user = result.data[0]

    if data.role == "opersac":
        perms = [{"user_id": new_id, "feature_key": f, "is_allowed": True} for f in PERMISSION_FEATURES]
        client.table("permissions").insert(perms).execute()

    AuditService().log(user=admin, action="CREATE_USER", entity_type="user", entity_id=new_id,
                       details={"username": data.username, "role": data.role})
    return user


@router.put("/{user_id}", response_model=UserResponse)
def update_user(user_id: uuid.UUID, data: UserUpdate, admin=Depends(require_admin)):
    client = get_subest_client()
    result = client.table("users").select("id").eq("id", str(user_id)).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    patch = {}
    if data.full_name is not None:
        patch["full_name"] = data.full_name
    if data.status is not None:
        if data.status not in ("active", "inactive", "reported"):
            raise HTTPException(status_code=400, detail="Estado invalido")
        patch["status"] = data.status
    if data.password is not None:
        patch["password_hash"] = data.password
    if data.email is not None:
        patch["email"] = data.email
    if data.phone is not None:
        patch["phone"] = data.phone

    if patch:
        client.table("users").update(patch).eq("id", str(user_id)).execute()

    updated = client.table("users").select("id,username,full_name,role,status,created_at,updated_at").eq("id", str(user_id)).execute()
    AuditService().log(user=admin, action="UPDATE_USER", entity_type="user", entity_id=str(user_id),
                       details={"updated_fields": list(patch.keys())})
    return updated.data[0]


@router.delete("/{user_id}")
def delete_user(user_id: uuid.UUID, admin=Depends(require_admin)):
    if user_id == admin.id:
        raise HTTPException(status_code=400, detail="No puedes eliminar tu propio usuario")

    client = get_subest_client()
    result = client.table("users").select("username").eq("id", str(user_id)).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    username = result.data[0]["username"]

    client.table("users").delete().eq("id", str(user_id)).execute()

    AuditService().log(user=admin, action="DELETE_USER", entity_type="user", entity_id=str(user_id),
                       details={"username": username})
    return {"message": "Usuario eliminado exitosamente"}
