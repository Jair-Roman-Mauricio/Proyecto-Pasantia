from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Observation(Base):
    __tablename__ = "observations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    circuit_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("circuits.id", ondelete="CASCADE"), nullable=True
    )
    sub_circuit_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("sub_circuits.id", ondelete="CASCADE"), nullable=True
    )
    bar_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("bars.id", ondelete="CASCADE"), nullable=True
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False
    )
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    circuit = relationship("Circuit", back_populates="observations")
    bar = relationship("Bar", back_populates="observations")
    user = relationship("User", back_populates="observations")
