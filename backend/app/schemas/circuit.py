from datetime import datetime, date
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel


class CircuitCreate(BaseModel):
    denomination: str
    name: str
    description: Optional[str] = None
    local_item: Optional[str] = None
    pi_kw: Decimal
    fd: Decimal = Decimal("1.0")
    md_kw: Optional[Decimal] = None  # auto-calculated if not provided
    status: str = "operative_normal"
    is_ups: bool = False
    secondary_bar_id: Optional[int] = None
    tertiary_bar_id: Optional[int] = None
    force: bool = False  # override energy check


class CircuitUpdate(BaseModel):
    denomination: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    local_item: Optional[str] = None
    pi_kw: Optional[Decimal] = None
    fd: Optional[Decimal] = None
    md_kw: Optional[Decimal] = None


class CircuitStatusUpdate(BaseModel):
    status: str  # operative_normal, reserve_r, reserve_equipped_re


class CircuitResponse(BaseModel):
    id: int
    bar_id: int
    secondary_bar_id: Optional[int] = None
    tertiary_bar_id: Optional[int] = None
    denomination: str
    name: str
    description: Optional[str] = None
    local_item: Optional[str] = None
    pi_kw: Decimal
    fd: Decimal
    md_kw: Decimal
    status: str
    is_ups: bool
    reserve_since: Optional[date] = None
    client_last_contact: Optional[date] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
