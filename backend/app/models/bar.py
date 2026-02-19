from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import String, Integer, Numeric, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Bar(Base):
    __tablename__ = "bars"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    station_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("stations.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    bar_type: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="operative")
    capacity_kw: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
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
    circuits = relationship(
        "Circuit",
        back_populates="bar",
        foreign_keys="Circuit.bar_id",
        cascade="all, delete-orphan",
    )
    secondary_circuits = relationship(
        "Circuit",
        back_populates="secondary_bar",
        foreign_keys="Circuit.secondary_bar_id",
    )
    tertiary_circuits = relationship(
        "Circuit",
        foreign_keys="Circuit.tertiary_bar_id",
    )
    observations = relationship("Observation", back_populates="bar")
