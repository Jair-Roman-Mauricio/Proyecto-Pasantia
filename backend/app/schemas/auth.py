from pydantic import BaseModel, field_validator


class UserBrief(BaseModel):
    id: str  # UUID serializado como string
    username: str
    full_name: str
    role: str

    @field_validator("id", mode="before")
    @classmethod
    def coerce_uuid(cls, v):
        return str(v)

    class Config:
        from_attributes = True
