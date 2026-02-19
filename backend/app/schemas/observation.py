from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ObservationCreate(BaseModel):
    severity: str  # urgent, warning, recommendation
    content: str
    circuit_id: Optional[int] = None
    sub_circuit_id: Optional[int] = None
    bar_id: Optional[int] = None


class ObservationResponse(BaseModel):
    id: int
    circuit_id: Optional[int] = None
    sub_circuit_id: Optional[int] = None
    bar_id: Optional[int] = None
    user_id: int
    user_name: Optional[str] = None
    user_role: Optional[str] = None
    severity: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True
