from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel


class RequestCreate(BaseModel):
    station_id: int
    bar_type: str  # normal, emergency, continuity
    circuit_id: Optional[int] = None
    local_item: Optional[str] = None
    requested_load_kw: Decimal
    fd: Decimal = Decimal("1.0")
    sub_circuit_name: Optional[str] = None
    sub_circuit_description: Optional[str] = None
    sub_circuit_itm: Optional[str] = None
    sub_circuit_mm2: Optional[str] = None
    justification: Optional[str] = None


class RequestReject(BaseModel):
    rejection_reason: str


class RequestResponse(BaseModel):
    id: int
    opersac_user_id: int
    opersac_name: Optional[str] = None
    station_id: int
    station_name: Optional[str] = None
    bar_type: str
    circuit_id: Optional[int] = None
    circuit_name: Optional[str] = None
    local_item: Optional[str] = None
    requested_load_kw: Decimal
    fd: Decimal
    sub_circuit_name: Optional[str] = None
    sub_circuit_description: Optional[str] = None
    sub_circuit_itm: Optional[str] = None
    sub_circuit_mm2: Optional[str] = None
    justification: Optional[str] = None
    status: str
    rejection_reason: Optional[str] = None
    reviewed_by: Optional[int] = None
    reviewed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
