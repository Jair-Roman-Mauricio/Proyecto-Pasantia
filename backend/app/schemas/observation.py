"""
Schemas Pydantic para el recurso Observación (Observation).

Define los modelos de creación y respuesta de las observaciones técnicas
que el personal puede registrar sobre circuitos, sub-circuitos y barras.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ObservationCreate(BaseModel):
    """
    Payload para registrar una nueva observación técnica.

    Usado por POST /observations.
    Debe asociarse al menos a una entidad: circuit_id, sub_circuit_id o bar_id.
    El campo `user_id` se extrae automáticamente del token JWT del usuario autenticado.
    """

    # Nivel de severidad: 'urgent', 'warning' o 'recommendation'
    severity: str
    content: str                                # Texto de la observación técnica
    circuit_id: Optional[int] = None           # ID del circuito al que aplica (exclusivo con los demás)
    sub_circuit_id: Optional[int] = None       # ID del sub-circuito al que aplica
    bar_id: Optional[int] = None               # ID de la barra al que aplica


class ObservationResponse(BaseModel):
    """
    Respuesta completa de una observación técnica.

    Retornado por GET /observations y GET /observations/{id}.
    Incluye información desnormalizada del usuario que la registró
    (user_name, user_role) para facilitar la visualización en el frontend
    sin requerir joins adicionales.
    """

    id: int
    circuit_id: Optional[int] = None          # ID del circuito asociado (si aplica)
    sub_circuit_id: Optional[int] = None      # ID del sub-circuito asociado (si aplica)
    bar_id: Optional[int] = None              # ID de la barra asociada (si aplica)
    user_id: int                               # ID del usuario que registró la observación
    user_name: Optional[str] = None           # Nombre completo del usuario (desnormalizado)
    user_role: Optional[str] = None           # Rol del usuario: 'admin' u 'opersac' (desnormalizado)
    severity: str                              # Severidad: 'urgent', 'warning' o 'recommendation'
    content: str                               # Texto de la observación
    created_at: datetime

    class Config:
        from_attributes = True
