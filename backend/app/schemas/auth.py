"""
Schemas Pydantic para autenticación (Auth).

Define los modelos de representación resumida de usuarios utilizados
en los contextos de autenticación y relaciones entre recursos.
"""

from pydantic import BaseModel, field_validator


class UserBrief(BaseModel):
    """
    Representación compacta de un usuario para contextos de autenticación.

    Usado como payload embebido en respuestas que requieren identificar al
    usuario autenticado sin exponer todos sus campos (p.ej. dentro de tokens
    decodificados o como referencia en otros recursos).
    El campo `id` es el UUID de Supabase Auth serializado como string.
    """

    id: str        # UUID de Supabase Auth serializado como string
    username: str
    full_name: str
    # Rol del usuario: 'admin' (acceso total) u 'opersac' (acceso por permisos)
    role: str

    @field_validator("id", mode="before")
    @classmethod
    def coerce_uuid(cls, v):
        """Convierte el UUID de Supabase (objeto UUID) a string para la serialización JSON."""
        return str(v)

    class Config:
        from_attributes = True
