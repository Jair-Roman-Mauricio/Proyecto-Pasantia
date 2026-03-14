"""
Helpers para la API Admin de Supabase Auth.

Permiten crear y eliminar usuarios en auth.users de Supabase
usando la Service Role Key (clave privada del backend).

Estos endpoints requieren la SERVICE_ROLE_KEY y nunca deben
exponerse al frontend.
"""

import httpx

from app.config import settings


async def create_supabase_auth_user(
    email: str,
    password: str,
    username: str = "",
    role: str = "",
) -> dict:
    """
    Crea un usuario en Supabase Auth (auth.users) vía la API Admin.

    Retorna el objeto de usuario de Supabase, que incluye el campo `id`
    (UUID) que se usará como PK en nuestra tabla `users`.

    Parámetros:
        email:    Email del usuario (se usa el esquema {username}@linea1metro.internal)
        password: Contraseña en texto plano.
        username: Nombre de usuario para almacenar en user_metadata.
        role:     Rol (admin/opersac) para almacenar en user_metadata.

    Lanza:
        httpx.HTTPStatusError si Supabase devuelve un error HTTP.
    """
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{settings.SUPABASE_URL}/auth/v1/admin/users",
            headers={
                "apikey": settings.SUPABASE_SERVICE_ROLE_KEY,
                "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "email": email,
                "password": password,
                "email_confirm": True,
                "user_metadata": {"username": username, "role": role},
            },
        )
    response.raise_for_status()
    return response.json()


async def delete_supabase_auth_user(user_uuid: str) -> None:
    """
    Elimina un usuario de Supabase Auth (auth.users) vía la API Admin.

    Parámetros:
        user_uuid: UUID del usuario a eliminar (string).

    Lanza:
        httpx.HTTPStatusError si Supabase devuelve un error HTTP.
    """
    async with httpx.AsyncClient() as client:
        response = await client.delete(
            f"{settings.SUPABASE_URL}/auth/v1/admin/users/{user_uuid}",
            headers={
                "apikey": settings.SUPABASE_SERVICE_ROLE_KEY,
                "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
            },
        )
    response.raise_for_status()
