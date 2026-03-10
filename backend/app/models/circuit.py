from datetime import datetime, date, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import String, Integer, Numeric, DateTime, Date, ForeignKey, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Circuit(Base):
    """
    Representa un circuito eléctrico dentro de una barra de una estación.

    La Demanda Máxima (MD) se calcula como MD = PI × FD, donde PI es la
    potencia instalada y FD es el factor de demanda. Solo los circuitos en
    estado 'operative_normal' contribuyen al cálculo energético de la estación.

    Un circuito puede estar alimentado desde una barra principal (bar_id) y
    opcionalmente tener una barra secundaria (is_ups=True requiere secondary_bar_id)
    y una barra terciaria de respaldo adicional.

    Estados posibles:
        - 'operative_normal': activo y contabilizado en el cálculo energético.
        - 'reserve_r': en reserva rotativa (no se suma al cálculo).
        - 'reserve_re': en reserva de emergencia (no se suma al cálculo).
        - 'inactive': fuera de servicio.
    """

    __tablename__ = "circuits"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    # Barra principal a la que pertenece el circuito (FK con eliminación en cascada)
    bar_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("bars.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # Barra secundaria requerida cuando el circuito es UPS (is_ups=True)
    secondary_bar_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("bars.id"), nullable=True
    )
    # Barra terciaria opcional para alimentación adicional de respaldo
    tertiary_bar_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("bars.id"), nullable=True
    )
    denomination: Mapped[str] = mapped_column(String(100), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    local_item: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    # Potencia instalada en kilovatios (base del cálculo de MD)
    pi_kw: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    # Factor de demanda entre 0 y 1; representa la fracción de PI efectivamente utilizada
    fd: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False, default=1.0)
    # Demanda máxima calculada: MD = PI × FD (actualizado por EnergyCalculator)
    md_kw: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    # Estado operativo del circuito (ver docstring de clase para valores válidos)
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="operative_normal", index=True
    )
    # Indica si el circuito es un sistema de alimentación ininterrumpida (UPS)
    is_ups: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # Fecha en que el circuito entró en estado de reserva
    reserve_since: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    # Fecha límite de la reserva; pasada esta fecha se genera una notificación
    reserve_expires_at: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    # Último contacto registrado con el cliente titular del circuito en reserva
    client_last_contact: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    bar = relationship("Bar", back_populates="circuits", foreign_keys=[bar_id])
    secondary_bar = relationship("Bar", back_populates="secondary_circuits", foreign_keys=[secondary_bar_id])
    tertiary_bar = relationship("Bar", back_populates="tertiary_circuits", foreign_keys=[tertiary_bar_id])
    sub_circuits = relationship("SubCircuit", back_populates="circuit", cascade="all, delete-orphan")
    observations = relationship("Observation", back_populates="circuit")
    notifications = relationship("Notification", back_populates="circuit")
