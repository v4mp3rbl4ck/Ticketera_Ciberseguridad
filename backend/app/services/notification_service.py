import smtplib
from datetime import datetime, timedelta
from app.core.timezone import now_utc_naive
from email.message import EmailMessage
from sqlalchemy import select, or_
from sqlalchemy.orm import Session, selectinload
from app.core.config import settings
from app.models.notification import Notification
from app.models.user import User
from app.models.ticket import Ticket, TicketComment
from app.services.sla_service import get_sla_snapshot

OPEN_STATUSES = ["Nuevo", "Asignado", "En Progreso", "En Espera"]


def create_notification(
    db: Session,
    *,
    user_id: int | None,
    title: str,
    body: str,
    channel: str = "in_app",
    kind: str | None = None,
    entity_type: str | None = None,
    entity_id: int | None = None,
    unique_key: str | None = None,
) -> Notification:
    if unique_key and user_id:
        existing = db.execute(
            select(Notification).where(Notification.user_id == user_id, Notification.unique_key == unique_key)
        ).scalar_one_or_none()
        if existing:
            return existing
    notification = Notification(
        user_id=user_id,
        title=title,
        body=body,
        channel=channel,
        kind=kind,
        entity_type=entity_type,
        entity_id=entity_id,
        unique_key=unique_key,
    )
    db.add(notification)
    db.flush()
    return notification


def send_email(to: str, subject: str, body: str) -> bool:
    """Envía correo si SMTP_ENABLED=true. Nunca rompe el flujo del ticket si falla SMTP."""
    if not settings.SMTP_ENABLED or not to:
        return False
    try:
        msg = EmailMessage()
        msg["From"] = settings.SMTP_FROM
        msg["To"] = to
        msg["Subject"] = subject
        msg.set_content(body)
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as smtp:
            if settings.SMTP_TLS:
                smtp.starttls()
            if settings.SMTP_USER:
                smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            smtp.send_message(msg)
        return True
    except Exception:
        return False


def _notify_user(
    db: Session,
    user: User | None,
    title: str,
    body: str,
    email_subject: str | None = None,
    *,
    kind: str | None = None,
    entity_type: str | None = None,
    entity_id: int | None = None,
    unique_key: str | None = None,
) -> None:
    if not user or not user.is_active or user.is_deleted:
        return
    create_notification(
        db,
        user_id=user.id,
        title=title,
        body=body,
        kind=kind,
        entity_type=entity_type,
        entity_id=entity_id,
        unique_key=unique_key,
    )
    send_email(user.email, email_subject or title, body)


def _unique_recipients(users: list[User | None], exclude_user_id: int | None = None) -> list[User]:
    seen: set[int] = set()
    output: list[User] = []
    for user in users:
        if not user or not user.id:
            continue
        if exclude_user_id and user.id == exclude_user_id:
            continue
        if user.id in seen:
            continue
        seen.add(user.id)
        output.append(user)
    return output


def notify_ticket_created(db: Session, ticket: Ticket, analysts: list[User]) -> None:
    title = f"Nuevo ticket {ticket.severity}"
    body = f"{ticket.ticket_number}: {ticket.subject}\nÁrea: {ticket.area_destino}\nCaso: {ticket.category}"
    for analyst in analysts:
        _notify_user(
            db,
            analyst,
            title,
            body,
            kind="ticket_created",
            entity_type="ticket",
            entity_id=ticket.id,
            unique_key=f"ticket:{ticket.id}:created:analyst:{analyst.id}",
        )


def notify_ticket_assigned(db: Session, ticket: Ticket) -> None:
    assigned_user = ticket.assigned_to
    if not assigned_user and ticket.assigned_to_id:
        assigned_user = db.get(User, ticket.assigned_to_id)
    _notify_user(
        db,
        assigned_user,
        f"Ticket asignado {ticket.ticket_number}",
        f"Se te asignó el ticket {ticket.ticket_number}: {ticket.subject}",
        kind="ticket_assigned",
        entity_type="ticket",
        entity_id=ticket.id,
        unique_key=f"ticket:{ticket.id}:assigned:{ticket.assigned_to_id}:{now_utc_naive().strftime('%Y%m%d%H%M%S')}",
    )


def notify_ticket_status_changed(db: Session, ticket: Ticket, *, old_status: str, new_status: str, actor: User) -> None:
    recipients = _unique_recipients([ticket.created_by, ticket.assigned_to], exclude_user_id=actor.id)
    for user in recipients:
        _notify_user(
            db,
            user,
            f"Estado actualizado {ticket.ticket_number}",
            f"{actor.full_name} cambió el estado de {ticket.ticket_number} de '{old_status}' a '{new_status}'.",
            kind="ticket_status_changed",
            entity_type="ticket",
            entity_id=ticket.id,
            unique_key=f"ticket:{ticket.id}:status:{new_status}:{user.id}:{now_utc_naive().strftime('%Y%m%d%H%M%S')}",
        )


def notify_ticket_commented(db: Session, ticket: Ticket, comment: TicketComment, author: User) -> None:
    if comment.comment_type == "internal":
        # Las notas internas no se notifican a solicitantes.
        if ticket.assigned_to_id and ticket.assigned_to_id != author.id:
            _notify_user(
                db,
                ticket.assigned_to,
                f"Nueva nota interna {ticket.ticket_number}",
                f"{author.full_name} agregó una nota interna.",
                kind="ticket_internal_note",
                entity_type="ticket",
                entity_id=ticket.id,
            )
        return
    recipients = _unique_recipients([ticket.created_by, ticket.assigned_to], exclude_user_id=author.id)
    for user in recipients:
        _notify_user(
            db,
            user,
            f"Nuevo comentario {ticket.ticket_number}",
            f"{author.full_name} comentó en {ticket.ticket_number}:\n\n{comment.body[:500]}",
            kind="ticket_comment",
            entity_type="ticket",
            entity_id=ticket.id,
        )


def notify_ticket_resolved(db: Session, ticket: Ticket) -> None:
    _notify_user(
        db,
        ticket.created_by,
        f"Ticket resuelto {ticket.ticket_number}",
        f"Tu ticket {ticket.ticket_number} fue marcado como Resuelto.",
        kind="ticket_resolved",
        entity_type="ticket",
        entity_id=ticket.id,
        unique_key=f"ticket:{ticket.id}:resolved:{ticket.created_by_id}",
    )


def notify_ticket_closed(db: Session, ticket: Ticket) -> None:
    _notify_user(
        db,
        ticket.created_by,
        f"Ticket cerrado {ticket.ticket_number}",
        f"Tu ticket {ticket.ticket_number} fue marcado como Cerrado.",
        kind="ticket_closed",
        entity_type="ticket",
        entity_id=ticket.id,
        unique_key=f"ticket:{ticket.id}:closed:{ticket.created_by_id}",
    )


def _visible_tickets_for_user(db: Session, user: User) -> list[Ticket]:
    query = select(Ticket).options(selectinload(Ticket.created_by), selectinload(Ticket.assigned_to)).where(Ticket.status.in_(OPEN_STATUSES))
    if user.role in ["admin", "supervisor"]:
        pass
    elif user.role == "analyst" and user.area:
        query = query.where(or_(Ticket.area_destino == user.area, Ticket.assigned_to_id == user.id, Ticket.created_by_id == user.id))
    else:
        query = query.where(Ticket.created_by_id == user.id)
    return list(db.execute(query).scalars().unique().all())


def refresh_sla_notifications_for_user(db: Session, user: User) -> None:
    """Genera alertas in-app de SLA al consultar el centro de notificaciones.

    No reemplaza a un scheduler real, pero permite tener alertas internas sin
    depender todavía de Celery/Cron. Las notificaciones usan unique_key para no
    duplicarse cada vez que el usuario abre la campana.
    """
    now = now_utc_naive()
    for ticket in _visible_tickets_for_user(db, user):
        snapshot = get_sla_snapshot(db, ticket, now)
        state = snapshot.get("sla_state")
        if state == "breached":
            _notify_user(
                db,
                user,
                f"SLA vencido {ticket.ticket_number}",
                f"El ticket {ticket.ticket_number} superó su fecha límite SLA.",
                kind="sla_breached",
                entity_type="ticket",
                entity_id=ticket.id,
                unique_key=f"ticket:{ticket.id}:sla_breached:user:{user.id}",
            )
        elif state == "warning_90":
            _notify_user(
                db,
                user,
                f"SLA al 90% {ticket.ticket_number}",
                f"El ticket {ticket.ticket_number} ya consumió el 90% de su SLA.",
                kind="sla_warning_90",
                entity_type="ticket",
                entity_id=ticket.id,
                unique_key=f"ticket:{ticket.id}:sla_warning_90:user:{user.id}",
            )
        elif state == "warning_75":
            _notify_user(
                db,
                user,
                f"SLA al 75% {ticket.ticket_number}",
                f"El ticket {ticket.ticket_number} ya consumió el 75% de su SLA.",
                kind="sla_warning_75",
                entity_type="ticket",
                entity_id=ticket.id,
                unique_key=f"ticket:{ticket.id}:sla_warning_75:user:{user.id}",
            )

        if snapshot.get("sla_first_response_breached"):
            _notify_user(
                db,
                user,
                f"Primera respuesta vencida {ticket.ticket_number}",
                f"El ticket {ticket.ticket_number} superó el SLA de primera respuesta.",
                kind="sla_first_response_breached",
                entity_type="ticket",
                entity_id=ticket.id,
                unique_key=f"ticket:{ticket.id}:sla_first_response_breached:user:{user.id}",
            )
