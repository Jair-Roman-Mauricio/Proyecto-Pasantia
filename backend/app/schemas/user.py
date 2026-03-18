"""
Schemas Pydantic para el recurso Usuario (User).

Define los modelos de creación, actualización y respuesta de los usuarios
del sistema. Los IDs de usuario son UUIDs generados por Supabase Auth.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, field_validator


class UserCreate(BaseModel):
    """
    Payload para crear un nuevo usuario en el sistema.

    Usado por POST /users (solo administradores).
    El backend crea primero el usuario en Supabase Auth y luego registra
    el perfil en la tabla local `users` con el UUID obtenido de Supabase.
    """

    username: str                       # Nombre de usuario único para el login interno
    password: str                       # Contraseña en texto plano (se almacena hasheada en Supabase Auth)
    full_name: str                      # Nombre completo para mostrar en la interfaz
    # Rol del usuario: 'admin' (acceso total) u 'opersac' (acceso por permisos)
    role: str
    email: Optional[str] = None        # Correo personal de contacto (opcional, no se usa para login)
    phone: Optional[str] = None        # Teléfono de contacto (opcional)


class UserUpdate(BaseModel):
    """
    Payload para actualizar el perfil de un usuario existente.

    Todos los campos son opcionales; solo se actualizan los proporcionados.
    Usado por PATCH /users/{id}.
    """

    full_name: Optional[str] = None
    # Nuevo estado de la cuenta: 'active', 'inactive' o 'reported'
    status: Optional[str] = None
    email: Optional[str] = None        # Correo personal de contacto
    phone: Optional[str] = None        # Teléfono de contacto


class UserResponse(BaseModel):
    """
    Respuesta completa del perfil de un usuario.

    Retornado por GET /users y GET /users/{id}.
    El campo `id` es el UUID de Supabase Auth serializado como string
    para garantizar compatibilidad con JSON estándar.
    """

    id: str            # UUID de Supabase Auth serializado como string
    username: str
    full_name: str
    # Rol del usuario: 'admin' u 'opersac'
    role: str
    # Estado de la cuenta: 'active', 'inactive' o 'reported'
    status: str
    created_at: datetime
    updated_at: datetime

    @field_validator("id", mode="before")
    @classmethod
    def coerce_uuid(cls, v):
        """Convierte el UUID de Supabase (objeto UUID) a string para la serialización JSON."""
        return str(v)

    class Config:
        from_attributes = True
