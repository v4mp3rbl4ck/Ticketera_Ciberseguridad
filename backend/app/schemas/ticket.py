from datetime import datetime
from pydantic import BaseModel, Field


class DynamicAnswerIn(BaseModel):
    model_config = {"extra": "forbid"}
    question_key: str
    question_text: str
    answer: str | None = None
    required: bool = True


class TicketCreate(BaseModel):
    model_config = {"extra": "forbid"}
    area_destino: str
    project_area: str = Field(min_length=2)
    category: str
    severity: str
    subject: str = Field(min_length=3, max_length=255)
    description: str = Field(min_length=5)
    involved_asset: str = Field(min_length=1)
    first_event_at: datetime | None = None
    evidence_summary: str | None = None
    ip_address: str | None = None
    hostname: str | None = None
    impact: str = Field(min_length=2)
    scope_users_affected: str = "1"
    deadline: datetime | None = None
    deadline_justification: str | None = None
    dynamic_answers: list[DynamicAnswerIn] = []


class TicketUpdate(BaseModel):
    model_config = {"extra": "forbid"}
    assigned_to_id: str | None = None
    category: str | None = None
    severity: str | None = None
    status: str | None = None
    impact: str | None = None
    deadline: datetime | None = None
    deadline_justification: str | None = None


class TicketStatusUpdate(BaseModel):
    model_config = {"extra": "forbid"}
    status: str
    reason: str | None = None


class TicketAssign(BaseModel):
    model_config = {"extra": "forbid"}
    assigned_to_id: str


class TicketCommentCreate(BaseModel):
    model_config = {"extra": "forbid"}
    comment_type: str = "public"
    body: str = Field(min_length=1)


class DynamicAnswerOut(BaseModel):
    id: int
    question_key: str
    question_text: str
    answer: str | None
    required: bool

    model_config = {"from_attributes": True}


class TicketAttachmentOut(BaseModel):
    id: str
    file_name: str
    content_type: str | None
    size_bytes: int
    created_at: datetime
    uploaded_by_id: str
    uploaded_by_name: str | None = None
    comment_id: str | None = None
    download_url: str

    model_config = {"from_attributes": True}


class TicketCommentOut(BaseModel):
    id: str
    author_id: str
    author_name: str | None = None
    comment_type: str
    body: str
    created_at: datetime
    attachments: list[TicketAttachmentOut] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class TicketOut(BaseModel):
    id: str
    ticket_number: str
    created_by_id: str
    created_by_name: str | None = None
    created_by_email: str | None = None
    assigned_to_id: str | None
    assigned_to_name: str | None = None
    assigned_to_email: str | None = None
    area_destino: str
    project_area: str
    category: str
    severity: str
    status: str
    subject: str
    description: str
    involved_asset: str
    first_event_at: datetime | None
    evidence_summary: str | None
    ip_address: str | None
    hostname: str | None
    impact: str
    scope_users_affected: str
    deadline: datetime | None
    deadline_justification: str | None
    created_at: datetime
    updated_at: datetime
    assigned_at: datetime | None
    first_response_at: datetime | None
    resolved_at: datetime | None
    closed_at: datetime | None
    sla_due_at: datetime | None
    sla_paused_seconds: int
    is_sla_breached: bool
    sla_policy_id: int | None = None
    sla_policy_scope: str | None = None
    sla_business_hours_only: bool | None = None
    sla_pause_allowed: bool | None = None
    sla_first_response_due_at: datetime | None = None
    sla_first_response_breached: bool = False
    sla_first_response_elapsed_percent: float | None = None
    sla_remaining_seconds: int | None = None
    sla_elapsed_percent: float | None = None
    sla_consumed_seconds: int | None = None
    sla_consumed_minutes: float | None = None
    ticket_age_seconds: int | None = None
    ticket_age_minutes: float | None = None
    ticket_measurement_end_at: datetime | None = None
    ticket_time_is_final: bool = False
    sla_paused_minutes: float | None = None
    sla_state: str | None = None
    sla_state_label: str | None = None
    sla_state_tone: str | None = None
    sla_warning_level: int = 0
    sla_is_paused: bool = False
    dynamic_answers: list[DynamicAnswerOut] = []
    comments: list[TicketCommentOut] = []
    attachments: list[TicketAttachmentOut] = []

    model_config = {"from_attributes": True}


class ChecklistQuestion(BaseModel):
    key: str
    text: str
    required: bool = True


class ChecklistResponse(BaseModel):
    area: str
    severity: str
    category: str | None = None
    channel: str | None = None
    sla_mode: str | None = None
    description: str | None = None
    use_cases: list[str] = []
    questions: list[ChecklistQuestion]
