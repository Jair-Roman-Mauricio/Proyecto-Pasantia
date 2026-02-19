from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class BackupCreate(BaseModel):
    description: Optional[str] = None
    includes_audit: bool = True


class BackupResponse(BaseModel):
    id: int
    created_by: int
    creator_name: Optional[str] = None
    file_name: str
    description: Optional[str] = None
    includes_audit: bool
    size_bytes: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True
