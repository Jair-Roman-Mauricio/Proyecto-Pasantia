from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import String, Integer, Numeric, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Station(Base):
    """
    Representa una estación de la Línea 1 del Metro de Lima.

    Almacena la capacidad energética del transformador y los valores calculados
    de demanda máxima y potencia disponible. El campo `status` se actualiza
    automáticamente tras cada recálculo energético realizado por EnergyCalculator.
    """

    __tablename__ = "stations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(10), unique=True, nullable=False)
    # Nombre oficial de la estación (p.ej. "Villa El Salvador")
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    # Posición en la línea: 1 = Villa El Salvador, 26 = Bayovar
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)
    # Capacidad total del transformador en kilovatios
    transformer_capacity_kw: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, default=0
    )
    # Suma de MD de todos los circuitos operativos (calculado automáticamente)
    max_demand_kw: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, default=0
    )
    # transformer_capacity_kw - max_demand_kw (puede ser negativo si hay sobrecarga)
    available_power_kw: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, default=0
    )
    # Estado energético: 'green' (normal), 'yellow' (<20% disponible), 'red' (energía negativa)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="green")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    bars = relationship("Bar", back_populates="station", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="station")
    requests = relationship("Request", back_populates="station")
