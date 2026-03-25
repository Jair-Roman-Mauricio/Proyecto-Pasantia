import uuid as uuid_lib
from types import SimpleNamespace

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.subest_client import get_public_client, get_subest_client
from app.utils.security import decode_supabase_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = decode_supabase_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )

    sub = payload.get("sub")
    if sub is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token invalido")

    client = get_public_client()
    result = client.rpc("get_user_by_id", {"p_id": sub}).execute()
    if not result.data:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario no encontrado")

    subest_user = result.data[0]
    if subest_user.get("status") != "active":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Usuario inactivo")

    try:
        user_uuid = uuid_lib.UUID(sub)
    except (ValueError, TypeError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token invalido")

    return SimpleNamespace(
        id=user_uuid,
        username=subest_user["username"],
        full_name=subest_user.get("full_name") or subest_user["username"],
        role=subest_user["role"],
        status=subest_user["status"],
        permissions=[],
    )


def require_admin(current_user=Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requieren permisos de administrador",
        )
    return current_user


def check_permission(feature_key: str):
    def _check(current_user=Depends(get_current_user)):
        if current_user.role == "admin":
            return current_user
        client = get_subest_client()
        result = (
            client.table("permissions")
            .select("is_allowed")
            .eq("user_id", str(current_user.id))
            .eq("feature_key", feature_key)
            .execute()
        )
        perm = result.data[0] if result.data else None
        if perm is None or not perm["is_allowed"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"No tiene permiso para: {feature_key}",
            )
        return current_user
    return _check
