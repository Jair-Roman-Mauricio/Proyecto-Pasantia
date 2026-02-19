from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel


class RequestCreate(BaseModel):
    station_id: int
    bar_type: str  # normal, emergency, continuity
    requested_load_kw: Decimal
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
    requested_load_kw: Decimal
    justification: Optional[str] = None
    status: str
    rejection_reason: Optional[str] = None
    reviewed_by: Optional[int] = None
    reviewed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
