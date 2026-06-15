from datetime import datetime
from app.core.timezone import now_utc_naive
from sqlalchemy import String, Boolean, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class CorporateArea(Base):
    __tablename__ = "corporate_areas"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc_naive)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc_naive, onupdate=now_utc_naive)
