from datetime import datetime
from app.core.timezone import now_utc_naive
from sqlalchemy import String, Boolean, DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class SLAPolicy(Base):
    __tablename__ = "sla_policies"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    area: Mapped[str | None] = mapped_column(String(100), nullable=True)
    severity: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    first_response_minutes: Mapped[int] = mapped_column(Integer, default=60)
    resolution_minutes: Mapped[int] = mapped_column(Integer, default=480)
    business_hours_only: Mapped[bool] = mapped_column(Boolean, default=True)
    pause_allowed: Mapped[bool] = mapped_column(Boolean, default=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc_naive)
