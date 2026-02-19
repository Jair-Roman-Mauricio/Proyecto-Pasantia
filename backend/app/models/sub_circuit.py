from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import String, Integer, Numeric, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class SubCircuit(Base):
    __tablename__ = "sub_circuits"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    circuit_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("circuits.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    itm: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    mm2: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    pi_kw: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    fd: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False, default=1.0)
    md_kw: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    circuit = relationship("Circuit", back_populates="sub_circuits")
