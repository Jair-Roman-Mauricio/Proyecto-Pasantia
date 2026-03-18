"""
Schemas Pydantic para el recurso Auditoría (AuditLog).

Define los modelos de respuesta y marcado de registros de auditoría
que registran todas las operaciones sensibles realizadas en el sistema.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class AuditLogResponse(BaseModel):
    """
    Respuesta completa de un registro de auditoría.

    Retornado por GET /audit-logs.
    Los campos `user_role` y `user_name` se almacenan de forma desnormalizada
    para preservar el contexto histórico aunque el usuario sea modificado o
    eliminado posteriormente.
    El campo `entity_id` es string para soportar tanto IDs enteros
    (circuitos, barras, estaciones) como UUIDs (usuarios de Supabase Auth).
    """

    id: int
    user_id: str                         # UUID de Supabase Auth del usuario que realizó la acción (string)
    user_role: str                        # Rol del usuario en el momento de la acción (desnormalizado)
    user_name: str                        # Nombre completo en el momento de la acción (desnormalizado)
    action_date: datetime                 # Fecha y hora UTC de la acción
    action: str                           # Descripción de la acción realizada (p.ej. 'CREATE_CIRCUIT')
    entity_type: str                      # Tipo de entidad afectada (p.ej. 'circuit', 'user', 'station')
    entity_id: Optional[str] = None      # ID de la entidad (int o UUID serializado como string)
    details: Optional[dict] = None       # Payload JSON con datos adicionales del contexto de la acción
    is_flagged: bool                      # True si el registro fue marcado para revisión manual
    flag_reason: Optional[str] = None    # Motivo del marcado (solo cuando is_flagged=True)

    class Config:
        from_attributes = True


class AuditFlagUpdate(BaseModel):
    """
    Payload para marcar o desmarcar un registro de auditoría para revisión.

    Usado por PATCH /audit-logs/{id}/flag.
    Permite a los administradores señalar acciones sospechosas o importantes
    para revisión posterior sin alterar el registro original.
    """

    is_flagged: bool                      # True para marcar; False para desmarcar
    flag_reason: Optional[str] = None    # Motivo del marcado (recomendado cuando is_flagged=True)
