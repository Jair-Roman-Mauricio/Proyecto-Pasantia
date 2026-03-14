import uuid as uuid_lib

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.permission import Permission
from app.utils.security import decode_supabase_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    """
    Dependencia de FastAPI que autentica al usuario a partir del token JWT de Supabase.

    Decodifica el token usando SUPABASE_JWT_SECRET, extrae el `sub` (UUID del usuario
    en auth.users), lo busca en nuestra tabla `users` y verifica que esté activo.

    Retorna:
        Instancia User del usuario autenticado.

    Lanza:
        HTTP 401 si el token es inválido, expirado o el usuario no existe en nuestra BD.
        HTTP 403 si el usuario está inactivo o reportado.
    """
    payload = decode_supabase_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )

    sub = payload.get("sub")
    if sub is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalido",
        )

    try:
        user_uuid = uuid_lib.UUID(sub)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalido",
        )

    user = db.query(User).filter(User.id == user_uuid).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado",
        )

    if user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario inactivo o reportado",
        )

    return user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """
    Dependencia que restringe el acceso a usuarios con rol admin.
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requieren permisos de administrador",
        )
    return current_user


def check_permission(feature_key: str):
    """
    Fábrica de dependencias que verifica si el usuario tiene habilitado un permiso específico.
    Los admins tienen acceso implícito a todos los permisos.
    """
    def _check(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> User:
        if current_user.role == "admin":
            return current_user

        perm = (
            db.query(Permission)
            .filter(
                Permission.user_id == current_user.id,
                Permission.feature_key == feature_key,
            )
            .first()
        )
        if perm is None or not perm.is_allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"No tiene permiso para: {feature_key}",
            )
        return current_user

    return _check
