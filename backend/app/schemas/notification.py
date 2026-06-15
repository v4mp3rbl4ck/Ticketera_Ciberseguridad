from datetime import datetime
from pydantic import BaseModel


class NotificationOut(BaseModel):
    id: int
    user_id: int | None = None
    channel: str = "in_app"
    title: str
    body: str
    read: bool
    kind: str | None = None
    entity_type: str | None = None
    entity_id: str | None = None
    unique_key: str | None = None
    created_at: datetime
    read_at: datetime | None = None

    model_config = {"from_attributes": True}


class NotificationListResponse(BaseModel):
    items: list[NotificationOut]
    unread_count: int
