from datetime import datetime
from app.core.timezone import now_utc_naive
from sqlalchemy import String, Text, DateTime, Boolean, Integer
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    channel: Mapped[str] = mapped_column(String(50), default="in_app", nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    kind: Mapped[str | None] = mapped_column(String(80), nullable=True)
    entity_type: Mapped[str | None] = mapped_column(String(80), nullable=True)
    entity_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    unique_key: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc_naive)
    read_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    def mark_read(self) -> None:
        if not self.read:
            self.read = True
            self.read_at = now_utc_naive()
