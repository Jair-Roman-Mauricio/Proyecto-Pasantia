from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class UserCreate(BaseModel):
    username: str
    password: str
    full_name: str
    role: str  # admin, opersac


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    status: Optional[str] = None
    password: Optional[str] = None


class UserResponse(BaseModel):
    id: int
    username: str
    full_name: str
    role: str
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
