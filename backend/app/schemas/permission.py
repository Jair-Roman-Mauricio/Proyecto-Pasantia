from pydantic import BaseModel


class PermissionUpdate(BaseModel):
    feature_key: str
    is_allowed: bool


class PermissionResponse(BaseModel):
    id: int
    user_id: int
    feature_key: str
    is_allowed: bool

    class Config:
        from_attributes = True


class PermissionsBulkUpdate(BaseModel):
    permissions: list[PermissionUpdate]
