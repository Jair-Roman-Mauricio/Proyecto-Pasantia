from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, field_validator


class UserCreate(BaseModel):
    username: str
    password: str
    full_name: str
    role: str  # admin, opersac


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    status: Optional[str] = None


class UserResponse(BaseModel):
    id: str  # UUID serializado como string
    username: str
    full_name: str
    role: str
    status: str
    created_at: datetime
    updated_at: datetime

    @field_validator("id", mode="before")
    @classmethod
    def coerce_uuid(cls, v):
        return str(v)

    class Config:
        from_attributes = True
