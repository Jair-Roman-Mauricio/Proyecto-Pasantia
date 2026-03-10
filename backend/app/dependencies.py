from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.permission import Permission
from app.utils.security import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    """
    Dependencia de FastAPI que autentica al usuario a partir del token JWT.

    Decodifica el token del header Authorization, valida que sea correcto y no
    esté expirado, recupera el usuario de la BD y verifica que esté activo.

    Retorna:
        Instancia User del usuario autenticado.

    Lanza:
        HTTP 401 si el token es inválido, expirado o el usuario no existe.
        HTTP 403 si el usuario está inactivo o reportado.
    """
    payload = decode_access_token(token)
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
        user_id = int(sub)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalido",
        )

    user = db.query(User).filter(User.id == user_id).first()
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

    Se usa en endpoints que solo deben ser accesibles por administradores
    (gestión de circuitos, aprobación de solicitudes, backups, etc.).

    Retorna:
        Instancia User del admin autenticado.

    Lanza:
        HTTP 403 si el usuario autenticado no tiene rol admin.
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
    Para usuarios OPERSAC, se consulta la tabla permissions y se verifica
    que `is_allowed` sea True para la clave indicada.

    Parámetros:
        feature_key: Clave del permiso a verificar (ej. 'view_circuits', 'send_requests').

    Retorna:
        Una dependencia de FastAPI que retorna el User autenticado si tiene permiso.

    Lanza:
        HTTP 403 si el usuario no tiene el permiso requerido.
    """
    def _check(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> User:
        # Los admins tienen acceso total sin necesidad de revisar la tabla permissions
        if current_user.role == "admin":
            return current_user

        # Verificar en la tabla permissions si el permiso está habilitado para el usuario
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
