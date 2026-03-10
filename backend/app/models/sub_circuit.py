from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import String, Integer, Numeric, DateTime, Date, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class SubCircuit(Base):
    """
    Representa un sub-circuito eléctrico dentro de un circuito principal.

    Un sub-circuito modela una carga derivada del circuito padre. Al igual que
    el circuito, su Demanda Máxima se calcula como MD = PI × FD. Los sub-circuitos
    pueden entrar en estado de reserva de forma independiente al circuito padre,
    con sus propios plazos de vigencia.

    Los campos `itm` y `mm2` registran las especificaciones técnicas del cable:
        - `itm`: referencia del interruptor termomagnético asociado al sub-circuito.
        - `mm2`: sección transversal del conductor en milímetros cuadrados.

    Estados posibles (campo `status`):
        - 'operative_normal': activo y en operación regular.
        - 'reserve_r': en reserva rotativa.
        - 'reserve_re': en reserva de emergencia.
        - 'inactive': fuera de servicio.
    """

    __tablename__ = "sub_circuits"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    # Circuito padre al que pertenece este sub-circuito (FK con eliminación en cascada)
    circuit_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("circuits.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # Referencia del interruptor termomagnético (especificación técnica del cable)
    itm: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    # Sección del conductor en mm² (especificación técnica del cable)
    mm2: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    # Potencia instalada del sub-circuito en kilovatios
    pi_kw: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    # Factor de demanda entre 0 y 1
    fd: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False, default=1.0)
    # Demanda máxima calculada: MD = PI × FD
    md_kw: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    # Estado operativo del sub-circuito (ver docstring de clase para valores válidos)
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="operative_normal", index=True
    )
    # Fecha en que el sub-circuito entró en estado de reserva
    reserve_since: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    # Fecha límite de la reserva del sub-circuito
    reserve_expires_at: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    circuit = relationship("Circuit", back_populates="sub_circuits")
