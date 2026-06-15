from datetime import datetime
from pydantic import BaseModel, Field


class SOSEventCreate(BaseModel):
    call_datetime: datetime
    caller_name: str = Field(min_length=2)
    leadership_contacted: str = Field(min_length=2)
    affected_area: str
    affected_service: str
    impact_summary: str = Field(min_length=5)
    actions_taken: str | None = None
    policy_activated: str | None = None
    evidence_summary: str | None = None
    tlp: str = "TLP:RED"
    status: str = "Registrado"


class SOSEventOut(BaseModel):
    id: int
    created_by_id: int
    call_datetime: datetime
    caller_name: str
    leadership_contacted: str
    affected_area: str
    affected_service: str
    impact_summary: str
    actions_taken: str | None
    policy_activated: str | None
    evidence_summary: str | None
    tlp: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}
