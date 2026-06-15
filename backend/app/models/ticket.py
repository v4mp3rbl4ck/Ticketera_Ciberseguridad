from datetime import datetime
from app.core.timezone import now_utc_naive
from sqlalchemy import String, Text, DateTime, Boolean, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.core.ids import generate_public_id


class Ticket(Base):
    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    public_id: Mapped[str] = mapped_column(String(80), unique=True, index=True, default=lambda: generate_public_id("ticket"), nullable=False)
    ticket_number: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)

    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    assigned_to_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)

    area_destino: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    project_area: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(255), nullable=False)
    severity: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    # Campo conservado a nivel de BD por compatibilidad, pero retirado de la UI y API pública v6.
    tlp: Mapped[str] = mapped_column(String(50), default="N/A", nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="Nuevo", index=True, nullable=False)

    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    involved_asset: Mapped[str] = mapped_column(String(500), nullable=False)
    first_event_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    evidence_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(100), nullable=True)
    hostname: Mapped[str | None] = mapped_column(String(255), nullable=True)

    impact: Mapped[str] = mapped_column(String(255), nullable=False)
    scope_users_affected: Mapped[str] = mapped_column(String(100), default="1", nullable=False)
    deadline: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    deadline_justification: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc_naive, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc_naive, onupdate=now_utc_naive)
    assigned_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    first_response_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    sla_due_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    sla_paused_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    sla_paused_seconds: Mapped[int] = mapped_column(Integer, default=0)
    is_sla_breached: Mapped[bool] = mapped_column(Boolean, default=False)

    created_by = relationship("User", foreign_keys=[created_by_id])
    assigned_to = relationship("User", foreign_keys=[assigned_to_id])
    comments = relationship("TicketComment", back_populates="ticket", cascade="all, delete-orphan")
    dynamic_answers = relationship("TicketDynamicAnswer", back_populates="ticket", cascade="all, delete-orphan")
    attachments = relationship("TicketAttachment", back_populates="ticket", cascade="all, delete-orphan")


class TicketComment(Base):
    __tablename__ = "ticket_comments"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    public_id: Mapped[str] = mapped_column(String(80), unique=True, index=True, default=lambda: generate_public_id("comment"), nullable=False)
    ticket_id: Mapped[int] = mapped_column(ForeignKey("tickets.id"), nullable=False)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    comment_type: Mapped[str] = mapped_column(String(50), default="public", nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc_naive)

    ticket = relationship("Ticket", back_populates="comments")
    author = relationship("User")
    attachments = relationship("TicketAttachment", back_populates="comment")


class TicketDynamicAnswer(Base):
    __tablename__ = "ticket_dynamic_answers"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    public_id: Mapped[str] = mapped_column(String(80), unique=True, index=True, default=lambda: generate_public_id("answer"), nullable=False)
    ticket_id: Mapped[int] = mapped_column(ForeignKey("tickets.id"), nullable=False)
    question_key: Mapped[str] = mapped_column(String(255), nullable=False)
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    required: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc_naive)

    ticket = relationship("Ticket", back_populates="dynamic_answers")


class TicketAttachment(Base):
    __tablename__ = "ticket_attachments"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    public_id: Mapped[str] = mapped_column(String(80), unique=True, index=True, default=lambda: generate_public_id("attachment"), nullable=False)
    ticket_id: Mapped[int] = mapped_column(ForeignKey("tickets.id"), nullable=False)
    comment_id: Mapped[int | None] = mapped_column(ForeignKey("ticket_comments.id"), nullable=True, index=True)
    uploaded_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    content_type: Mapped[str | None] = mapped_column(String(255), nullable=True)
    detected_mime: Mapped[str | None] = mapped_column(String(255), nullable=True)
    sha256_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    security_scan_status: Mapped[str] = mapped_column(String(50), default="validated", nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc_naive)

    ticket = relationship("Ticket", back_populates="attachments")
    comment = relationship("TicketComment", back_populates="attachments")
    uploaded_by = relationship("User")
