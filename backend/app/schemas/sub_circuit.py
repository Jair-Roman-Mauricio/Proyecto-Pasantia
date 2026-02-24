from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel


class SubCircuitCreate(BaseModel):
    name: str
    description: Optional[str] = None
    itm: Optional[str] = None
    mm2: Optional[str] = None
    pi_kw: Decimal
    fd: Decimal = Decimal("1.0")
    md_kw: Optional[Decimal] = None
    status: str = "operative_normal"
    reserve_expires_at: Optional[date] = None


class SubCircuitUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    itm: Optional[str] = None
    mm2: Optional[str] = None
    pi_kw: Optional[Decimal] = None
    fd: Optional[Decimal] = None
    md_kw: Optional[Decimal] = None


class SubCircuitResponse(BaseModel):
    id: int
    circuit_id: int
    name: str
    description: Optional[str] = None
    itm: Optional[str] = None
    mm2: Optional[str] = None
    pi_kw: Decimal
    fd: Decimal
    md_kw: Decimal
    status: str
    reserve_since: Optional[date] = None
    reserve_expires_at: Optional[date] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SubCircuitStatusUpdate(BaseModel):
    status: str
    reserve_expires_at: Optional[date] = None
