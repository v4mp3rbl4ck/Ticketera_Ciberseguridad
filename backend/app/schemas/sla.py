from pydantic import BaseModel


class SLAPolicyCreate(BaseModel):
    area: str | None = None
    severity: str
    first_response_minutes: int
    resolution_minutes: int
    business_hours_only: bool = True
    pause_allowed: bool = True
    active: bool = True


class SLAPolicyUpdate(BaseModel):
    area: str | None = None
    severity: str | None = None
    first_response_minutes: int | None = None
    resolution_minutes: int | None = None
    business_hours_only: bool | None = None
    pause_allowed: bool | None = None
    active: bool | None = None


class SLAPolicyOut(BaseModel):
    id: int
    area: str | None
    severity: str
    first_response_minutes: int
    resolution_minutes: int
    business_hours_only: bool
    pause_allowed: bool
    active: bool

    model_config = {"from_attributes": True}
