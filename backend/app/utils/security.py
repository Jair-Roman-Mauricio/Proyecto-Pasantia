from datetime import datetime, timedelta, timezone

import bcrypt
from jose import JWTError, jwt

from app.config import settings


def hash_password(password: str) -> str:
    """
    Genera un hash seguro de la contraseña usando bcrypt con salt aleatorio.

    Parámetros:
        password: Contraseña en texto plano.

    Retorna:
        Cadena con el hash bcrypt listo para almacenar en la base de datos.
    """
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifica si una contraseña en texto plano coincide con su hash almacenado.

    Parámetros:
        plain_password:  Contraseña ingresada por el usuario en el login.
        hashed_password: Hash bcrypt almacenado en la base de datos.

    Retorna:
        True si la contraseña es correcta, False en caso contrario.
    """
    return bcrypt.checkpw(
        plain_password.encode("utf-8"), hashed_password.encode("utf-8")
    )


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """
    Genera un token JWT firmado con los datos proporcionados.

    Incluye automáticamente el campo de expiración (`exp`). Si no se especifica
    `expires_delta`, se usa el valor configurado en ACCESS_TOKEN_EXPIRE_MINUTES.

    Parámetros:
        data:          Payload del token (debe incluir al menos `sub` con el ID del usuario).
        expires_delta: Duración personalizada de validez del token.

    Retorna:
        Cadena con el token JWT codificado y firmado.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> dict | None:
    """
    Decodifica y valida un token JWT.

    Verifica la firma y la expiración usando la clave secreta configurada.

    Parámetros:
        token: Cadena JWT recibida en el header Authorization.

    Retorna:
        Diccionario con el payload si el token es válido, None si es inválido o expirado.
    """
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError as e:
        print(f"[JWT ERROR] {e}")
        return None
