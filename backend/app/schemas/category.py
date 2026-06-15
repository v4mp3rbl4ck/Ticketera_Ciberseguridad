from pydantic import BaseModel, Field


class CategoryCreate(BaseModel):
    area: str
    severity: str
    name: str = Field(min_length=2, max_length=255)
    description: str | None = None
    is_active: bool = True


class CategoryUpdate(BaseModel):
    area: str | None = None
    severity: str | None = None
    name: str | None = Field(default=None, min_length=2, max_length=255)
    description: str | None = None
    is_active: bool | None = None


class CategoryOut(BaseModel):
    id: int
    area: str
    severity: str
    name: str
    description: str | None = None
    is_active: bool

    model_config = {"from_attributes": True}
