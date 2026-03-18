"""
Schemas Pydantic para el recurso Notificación (Notification).

Define los modelos de respuesta y extensión de reserva para las
notificaciones automáticas generadas por el sistema.
"""

from datetime import datetime, date
from typing import Optional

from pydantic import BaseModel


class NotificationResponse(BaseModel):
    """
    Respuesta completa de una notificación del sistema.

    Retornado por GET /notifications.
    Las notificaciones se generan automáticamente por eventos del sistema,
    como sobrecarga de transformadores o reservas próximas a vencer.
    """

    id: int
    station_id: Optional[int] = None           # ID de la estación relacionada (si aplica)
    circuit_id: Optional[int] = None           # ID del circuito relacionado (si aplica)
    # Tipo de evento: 'negative_energy', 'reserve_no_contact', 'request_pending' o 'system'
    type: str
    message: str                                # Texto descriptivo del evento
    is_read: bool                               # True si el usuario ya leyó la notificación
    is_dismissed: bool                          # True si el usuario descartó la notificación
    extended_until: Optional[date] = None       # Fecha hasta la que se extendió la reserva (solo 'reserve_no_contact')
    auto_delete_at: Optional[date] = None       # Fecha de eliminación automática programada
    created_at: datetime

    class Config:
        from_attributes = True


class NotificationExtend(BaseModel):
    """
    Payload para extender la fecha de vencimiento de una reserva desde una notificación.

    Usado por POST /notifications/{id}/extend.
    Permite al administrador otorgar una prórroga al circuito en reserva
    que originó la notificación de tipo 'reserve_no_contact'.
    """

    extended_until: date  # Nueva fecha límite de la reserva (debe ser futura)
