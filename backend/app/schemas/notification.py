from datetime import datetime, date
from typing import Optional

from pydantic import BaseModel


class NotificationResponse(BaseModel):
    id: int
    station_id: Optional[int] = None
    circuit_id: Optional[int] = None
    type: str
    message: str
    is_read: bool
    is_dismissed: bool
    extended_until: Optional[date] = None
    auto_delete_at: Optional[date] = None
    created_at: datetime

    class Config:
        from_attributes = True


class NotificationExtend(BaseModel):
    extended_until: date
