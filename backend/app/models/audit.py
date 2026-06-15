from datetime import datetime
from app.core.timezone import now_utc_naive
from sqlalchemy import String, Text, DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=now_utc_naive, index=True)
    actor_user_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    actor_role: Mapped[str | None] = mapped_column(String(50), nullable=True)
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(100), nullable=False)
    action: Mapped[str] = mapped_column(String(255), nullable=False)
    old_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    new_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_ip: Mapped[str | None] = mapped_column(String(100), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)
    previous_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    current_hash: Mapped[str] = mapped_column(String(128), nullable=False)
