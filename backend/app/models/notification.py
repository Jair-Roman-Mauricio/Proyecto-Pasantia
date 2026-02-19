from datetime import datetime, date, timezone
from typing import Optional

from sqlalchemy import String, Integer, Boolean, DateTime, Date, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    station_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("stations.id"), nullable=True
    )
    circuit_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("circuits.id"), nullable=True
    )
    type: Mapped[str] = mapped_column(String(30), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    is_dismissed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    extended_until: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    auto_delete_at: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    station = relationship("Station", back_populates="notifications")
    circuit = relationship("Circuit", back_populates="notifications")
