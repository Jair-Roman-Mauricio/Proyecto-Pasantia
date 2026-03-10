from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import String, Integer, Numeric, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Bar(Base):
    """
    Representa una barra eléctrica perteneciente a una estación.

    Una barra agrupa circuitos según su función dentro del sistema eléctrico.
    El campo `bar_type` distingue entre los tipos de barra disponibles:
        - 'normal': barra de alimentación principal.
        - 'emergencia': barra para suministro durante fallos del sistema principal.
        - 'continuidad': barra para cargas críticas que no toleran interrupciones.

    Cada circuito referencia su barra primaria obligatoria mediante `bar_id`;
    adicionalmente puede referenciar esta barra como barra secundaria o terciaria
    a través de las relaciones `secondary_circuits` y `tertiary_circuits`.
    """

    __tablename__ = "bars"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    station_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("stations.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    # Categoría funcional de la barra: 'normal', 'emergencia' o 'continuidad'
    bar_type: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="operative")
    # Capacidad máxima de la barra expresada en kilovatios
    capacity_kw: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    # Capacidad máxima de la barra expresada en amperios
    capacity_a: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    station = relationship("Station", back_populates="bars")
    # Circuitos cuya barra principal es esta barra (relación primaria)
    circuits = relationship(
        "Circuit",
        back_populates="bar",
        foreign_keys="Circuit.bar_id",
        cascade="all, delete-orphan",
    )
    # Circuitos que usan esta barra como alimentación secundaria (p.ej. UPS)
    secondary_circuits = relationship(
        "Circuit",
        back_populates="secondary_bar",
        foreign_keys="Circuit.secondary_bar_id",
    )
    # Circuitos que usan esta barra como alimentación terciaria de respaldo
    tertiary_circuits = relationship(
        "Circuit",
        back_populates="tertiary_bar",
        foreign_keys="Circuit.tertiary_bar_id",
    )
    observations = relationship("Observation", back_populates="bar")
