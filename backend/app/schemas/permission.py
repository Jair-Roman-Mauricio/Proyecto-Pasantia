"""
Schemas Pydantic para el recurso Permiso (Permission).

Define los modelos de actualización individual, respuesta y actualización
masiva de los permisos granulares asignados a usuarios Opersac.
"""

from pydantic import BaseModel, field_validator


class PermissionUpdate(BaseModel):
    """
    Payload para actualizar un permiso individual de un usuario.

    Representa la habilitación o deshabilitación de una funcionalidad
    específica para un usuario Opersac.
    Usado dentro de PermissionsBulkUpdate o de forma individual.
    """

    # Clave de la funcionalidad controlada (p.ej. 'view_stations', 'send_requests', 'view_reports')
    feature_key: str
    is_allowed: bool  # True para habilitar el acceso; False para denegarlo explícitamente


class PermissionResponse(BaseModel):
    """
    Respuesta de un permiso asignado a un usuario.

    Retornado por GET /users/{id}/permissions.
    El campo `user_id` es el UUID de Supabase Auth serializado como string.
    """

    id: int
    user_id: str        # UUID de Supabase Auth del usuario Opersac (serializado como string)
    # Clave de la funcionalidad: 'view_stations', 'send_requests', 'view_reports', etc.
    feature_key: str
    is_allowed: bool    # True si el acceso está habilitado

    @field_validator("user_id", mode="before")
    @classmethod
    def coerce_uuid(cls, v):
        """Convierte el UUID de Supabase (objeto UUID) a string para la serialización JSON."""
        return str(v)

    class Config:
        from_attributes = True


class PermissionsBulkUpdate(BaseModel):
    """
    Payload para actualizar múltiples permisos de un usuario en una sola operación.

    Usado por PUT /users/{id}/permissions.
    Reemplaza todos los permisos existentes del usuario con la lista proporcionada,
    garantizando un estado consistente sin requerir múltiples llamadas a la API.
    """

    permissions: list[PermissionUpdate]  # Lista de permisos a aplicar al usuario
