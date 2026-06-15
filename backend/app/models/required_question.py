from datetime import datetime
from app.core.timezone import now_utc_naive
from sqlalchemy import String, Text, Boolean, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class RequiredQuestion(Base):
    __tablename__ = "required_questions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    area: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    severity: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    category: Mapped[str] = mapped_column(String(255), default="*", index=True, nullable=False)
    question_key: Mapped[str] = mapped_column(String(255), nullable=False)
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    required: Mapped[bool] = mapped_column(Boolean, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc_naive)
