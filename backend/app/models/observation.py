from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Observation(Base):
    """
    Observación técnica registrada por un usuario sobre una entidad del sistema.

    Las observaciones documentan hallazgos, anomalías o notas operativas
    asociadas a circuitos, sub-circuitos o barras. Cada observación pertenece
    a exactamente uno de estos tres tipos de entidades; los otros dos campos
    de FK permanecen en None.

    Niveles de severidad (campo `severity`):
        - 'info': nota informativa sin impacto operativo.
        - 'warning': situación que requiere monitoreo o atención próxima.
        - 'critical': problema grave que exige acción inmediata.

    Las observaciones son inmutables una vez creadas (no tienen `updated_at`);
    para corregir una observación se debe crear una nueva entrada.
    """

    __tablename__ = "observations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    # Circuito al que se asocia la observación (exclusivo con sub_circuit_id y bar_id)
    circuit_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("circuits.id", ondelete="CASCADE"), nullable=True
    )
    # Sub-circuito al que se asocia la observación (exclusivo con circuit_id y bar_id)
    sub_circuit_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("sub_circuits.id", ondelete="CASCADE"), nullable=True
    )
    # Barra a la que se asocia la observación (exclusivo con circuit_id y sub_circuit_id)
    bar_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("bars.id", ondelete="CASCADE"), nullable=True
    )
    # Usuario que registró la observación
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False
    )
    # Nivel de severidad: 'info', 'warning' o 'critical'
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    circuit = relationship("Circuit", back_populates="observations")
    bar = relationship("Bar", back_populates="observations")
    user = relationship("User", back_populates="observations")
