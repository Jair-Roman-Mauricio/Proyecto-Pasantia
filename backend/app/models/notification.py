from datetime import datetime, date, timezone
from typing import Optional

from sqlalchemy import String, Integer, Boolean, DateTime, Date, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Notification(Base):
    """
    Representa una notificación generada automáticamente por el sistema.

    Las notificaciones alertan al personal sobre situaciones que requieren
    atención operativa. Se asocian opcionalmente a una estación y/o a un
    circuito específico según el evento que las originó.

    Tipos de notificación (campo `type`):
        - 'negative_energy': la potencia disponible de una estación es negativa,
          indicando sobrecarga del transformador.
        - 'reserve_no_contact': un circuito en reserva superó el plazo sin que
          se registrara contacto con el cliente titular.

    El campo `extended_until` se rellena cuando un administrador aprueba una
    extensión del período de reserva de un circuito.
    """

    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    station_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("stations.id"), nullable=True
    )
    circuit_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("circuits.id"), nullable=True
    )
    # Categoría del evento: 'negative_energy' o 'reserve_no_contact'
    type: Mapped[str] = mapped_column(String(30), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    # Indica si el usuario ya leyó la notificación (indexado para filtrar no leídas)
    is_read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    # Indica si el usuario descartó la notificación de su bandeja
    is_dismissed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # Fecha hasta la que se extendió la reserva del circuito (solo para 'reserve_no_contact')
    extended_until: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    # Fecha en que la notificación será eliminada automáticamente del sistema
    auto_delete_at: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    station = relationship("Station", back_populates="notifications")
    circuit = relationship("Circuit", back_populates="notifications")
