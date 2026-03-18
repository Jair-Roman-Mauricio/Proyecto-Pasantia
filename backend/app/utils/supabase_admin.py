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
    full_name: str = "",
    phone: str = "",
    contact_email: str = "",
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
                **({"phone": phone} if phone else {}),
                "user_metadata": {
                    "username": username,
                    "role": role,
                    "full_name": full_name,
                    **({"contact_email": contact_email} if contact_email else {}),
                },
            },
        )
    response.raise_for_status()
    return response.json()


async def update_supabase_auth_user(
    user_uuid: str,
    phone: str = "",
    contact_email: str = "",
) -> None:
    """
    Actualiza teléfono y/o correo de contacto de un usuario en Supabase Auth vía la API Admin.
    """
    payload: dict = {}
    if phone:
        payload["phone"] = phone
    meta: dict = {}
    if contact_email:
        meta["contact_email"] = contact_email
    if meta:
        payload["user_metadata"] = meta

    if not payload:
        return

    async with httpx.AsyncClient() as client:
        response = await client.put(
            f"{settings.SUPABASE_URL}/auth/v1/admin/users/{user_uuid}",
            headers={
                "apikey": settings.SUPABASE_SERVICE_ROLE_KEY,
                "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
                "Content-Type": "application/json",
            },
            json=payload,
        )
    response.raise_for_status()


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
