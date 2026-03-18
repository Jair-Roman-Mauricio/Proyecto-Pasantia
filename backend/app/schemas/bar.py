"""
Schemas Pydantic para el recurso Barra (Bar).

Define los modelos de actualización y respuesta de las barras eléctricas
que pertenecen a cada estación (normal, emergencia, continuidad).
"""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class BarUpdate(BaseModel):
    """
    Payload para actualizar las capacidades de una barra eléctrica.

    Usado por PATCH /bars/{id}. Ambos campos son requeridos cuando se envía
    la solicitud de actualización.
    """

    capacity_kw: Decimal   # Nueva capacidad máxima de la barra en kilovatios
    capacity_a: Decimal    # Nueva capacidad máxima de la barra en amperios


class BarResponse(BaseModel):
    """
    Respuesta completa de una barra eléctrica.

    Retornado por GET /bars y GET /bars/{id}.
    Incluye el tipo de barra (normal/emergency/continuity) y su estado operativo.
    """

    id: int
    station_id: int        # ID de la estación a la que pertenece la barra
    name: str              # Nombre descriptivo de la barra (p.ej. "Barra Normal Principal")
    bar_type: str          # Tipo: 'normal', 'emergency' o 'continuity'
    status: str            # Estado operativo: 'operative' o 'inactive'
    capacity_kw: Decimal   # Capacidad máxima en kilovatios
    capacity_a: Decimal    # Capacidad máxima en amperios
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
