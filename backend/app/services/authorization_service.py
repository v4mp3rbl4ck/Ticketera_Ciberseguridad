from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload
from app.models.user import User
from app.models.ticket import Ticket, TicketAttachment, TicketComment
from app.services.audit_service import write_audit
from app.services.role_service import has_permission


def has_global_ticket_scope(db: Session, user: User) -> bool:
    return user.role in ["admin", "supervisor"] or has_permission(db, user, "tickets", "edit")


def can_view_ticket(db: Session, user: User, ticket: Ticket) -> bool:
    if has_global_ticket_scope(db, user):
        return True
    if ticket.created_by_id == user.id:
        return True
    if user.role == "analyst" and user.area:
        return ticket.area_destino == user.area or ticket.assigned_to_id == user.id
    return False


def can_manage_ticket(db: Session, user: User, ticket: Ticket) -> bool:
    if user.role == "admin":
        return True
    if not has_permission(db, user, "tickets", "edit"):
        return False
    if user.role == "analyst" and user.area:
        return ticket.area_destino == user.area or ticket.assigned_to_id == user.id
    return user.role in ["supervisor"]


def can_download_attachment(db: Session, user: User, attachment: TicketAttachment) -> bool:
    if not can_view_ticket(db, user, attachment.ticket):
        return False
    if user.role == "requester" and attachment.comment and attachment.comment.comment_type == "internal":
        return False
    return True


def can_view_user(db: Session, user: User, target: User) -> bool:
    if user.id == target.id:
        return True
    return has_permission(db, user, "admin_users", "view")


def can_edit_user(db: Session, user: User, target: User) -> bool:
    if user.id == target.id:
        return False
    return has_permission(db, user, "admin_users", "edit")


def deny_with_audit(db: Session, *, actor: User | None, entity_type: str, entity_id: str | int, action: str, detail: str = "Recurso no encontrado") -> None:
    try:
        write_audit(db, actor=actor, entity_type=entity_type, entity_id=entity_id, action=action, new_value="denied")
        db.commit()
    except Exception:
        db.rollback()
    # 404 reduce enumeración de objetos no permitidos.
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


def ticket_query_with_relations():
    return select(Ticket).options(
        selectinload(Ticket.created_by),
        selectinload(Ticket.assigned_to),
        selectinload(Ticket.dynamic_answers),
        selectinload(Ticket.comments).selectinload(TicketComment.author),
        selectinload(Ticket.comments).selectinload(TicketComment.attachments).selectinload(TicketAttachment.uploaded_by),
        selectinload(Ticket.attachments).selectinload(TicketAttachment.uploaded_by),
    )


def get_ticket_by_public_ref(db: Session, ref: str | int) -> Ticket | None:
    value = str(ref)
    query = ticket_query_with_relations()
    ticket = db.execute(query.where(Ticket.public_id == value)).scalar_one_or_none()
    if ticket:
        return ticket
    # Compatibilidad temporal con enlaces antiguos numéricos. No se debe usar desde frontend.
    if value.isdigit():
        return db.execute(query.where(Ticket.id == int(value))).scalar_one_or_none()
    return None


def require_view_ticket(db: Session, user: User, ref: str | int) -> Ticket:
    ticket = get_ticket_by_public_ref(db, ref)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")
    if not can_view_ticket(db, user, ticket):
        deny_with_audit(db, actor=user, entity_type="ticket", entity_id=getattr(ticket, "public_id", ticket.id), action="ticket_access_denied")
    return ticket


def require_manage_ticket(db: Session, user: User, ref: str | int) -> Ticket:
    ticket = require_view_ticket(db, user, ref)
    if not can_manage_ticket(db, user, ticket):
        deny_with_audit(db, actor=user, entity_type="ticket", entity_id=getattr(ticket, "public_id", ticket.id), action="ticket_manage_denied")
    return ticket


def resolve_user_ref(db: Session, ref: str | int | None) -> User | None:
    if ref is None:
        return None
    value = str(ref)
    user = db.execute(select(User).where(User.public_id == value)).scalar_one_or_none()
    if user:
        return user
    if value.isdigit():
        return db.get(User, int(value))
    return None
