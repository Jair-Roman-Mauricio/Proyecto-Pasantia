from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class AuditLogResponse(BaseModel):
    id: int
    user_id: str  # UUID serializado como string
    user_role: str
    user_name: str
    action_date: datetime
    action: str
    entity_type: str
    entity_id: Optional[str] = None  # String para soportar int IDs y UUIDs
    details: Optional[dict] = None
    is_flagged: bool
    flag_reason: Optional[str] = None

    class Config:
        from_attributes = True


class AuditFlagUpdate(BaseModel):
    is_flagged: bool
    flag_reason: Optional[str] = None
