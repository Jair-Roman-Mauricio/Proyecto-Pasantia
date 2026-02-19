from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import String, Integer, Numeric, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Request(Base):
    __tablename__ = "requests"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    opersac_user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False
    )
    station_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("stations.id"), nullable=False
    )
    bar_type: Mapped[str] = mapped_column(String(20), nullable=False)
    requested_load_kw: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False
    )
    justification: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending", index=True
    )
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reviewed_by: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True
    )
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    opersac_user = relationship("User", foreign_keys=[opersac_user_id])
    reviewer = relationship("User", foreign_keys=[reviewed_by])
    station = relationship("Station", back_populates="requests")
