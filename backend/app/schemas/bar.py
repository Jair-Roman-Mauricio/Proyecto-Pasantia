from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class BarResponse(BaseModel):
    id: int
    station_id: int
    name: str
    bar_type: str
    status: str
    capacity_kw: Decimal
    capacity_a: Decimal
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
