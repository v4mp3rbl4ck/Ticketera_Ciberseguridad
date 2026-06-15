from datetime import datetime
from pydantic import BaseModel, Field


class CorporateAreaCreate(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    description: str | None = None
    is_active: bool = True


class CorporateAreaUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=255)
    description: str | None = None
    is_active: bool | None = None


class CorporateAreaOut(BaseModel):
    id: int
    name: str
    description: str | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
