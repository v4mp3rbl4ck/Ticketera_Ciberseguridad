from datetime import datetime
from app.core.timezone import now_utc_naive
from sqlalchemy import String, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class SOSEvent(Base):
    __tablename__ = "sos_events"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    call_datetime: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    caller_name: Mapped[str] = mapped_column(String(255), nullable=False)
    leadership_contacted: Mapped[str] = mapped_column(String(255), nullable=False)
    affected_area: Mapped[str] = mapped_column(String(255), nullable=False)
    affected_service: Mapped[str] = mapped_column(String(255), nullable=False)
    impact_summary: Mapped[str] = mapped_column(Text, nullable=False)
    actions_taken: Mapped[str | None] = mapped_column(Text, nullable=True)
    policy_activated: Mapped[str | None] = mapped_column(String(255), nullable=True)
    evidence_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    tlp: Mapped[str] = mapped_column(String(50), default="TLP:RED", nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="Registrado", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc_naive)

    created_by = relationship("User")
