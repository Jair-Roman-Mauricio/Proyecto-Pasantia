from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import String, Integer, Numeric, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Station(Base):
    __tablename__ = "stations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(10), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)
    transformer_capacity_kw: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, default=0
    )
    max_demand_kw: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, default=0
    )
    available_power_kw: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, default=0
    )
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
