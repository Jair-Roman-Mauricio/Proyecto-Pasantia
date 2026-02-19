from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class AuditLogResponse(BaseModel):
    id: int
    user_id: int
    user_role: str
    user_name: str
    action_date: datetime
    action: str
    entity_type: str
    entity_id: Optional[int] = None
    details: Optional[dict] = None
    is_flagged: bool
    flag_reason: Optional[str] = None

    class Config:
        from_attributes = True


class AuditFlagUpdate(BaseModel):
    is_flagged: bool
    flag_reason: Optional[str] = None
