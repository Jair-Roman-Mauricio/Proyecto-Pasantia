from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel


class StationResponse(BaseModel):
    id: int
    code: str
    name: str
    order_index: int
    transformer_capacity_kw: Decimal
    max_demand_kw: Decimal
    available_power_kw: Decimal
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class StationUpdate(BaseModel):
    transformer_capacity_kw: Optional[Decimal] = None
    max_demand_kw: Optional[Decimal] = None


class PowerSummary(BaseModel):
    station_id: int
    station_name: str
    transformer_capacity_kw: Decimal
    max_demand_kw: Decimal
    available_power_kw: Decimal
    status: str
