from datetime import datetime, date, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import String, Integer, Numeric, DateTime, Date, ForeignKey, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Circuit(Base):
    __tablename__ = "circuits"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    bar_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("bars.id", ondelete="CASCADE"), nullable=False, index=True
    )
    secondary_bar_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("bars.id"), nullable=True
    )
    denomination: Mapped[str] = mapped_column(String(100), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    local_item: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    pi_kw: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    fd: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False, default=1.0)
    md_kw: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="operative_normal", index=True
    )
    is_ups: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    reserve_since: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
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
    sub_circuits = relationship("SubCircuit", back_populates="circuit", cascade="all, delete-orphan")
    observations = relationship("Observation", back_populates="circuit")
    notifications = relationship("Notification", back_populates="circuit")
