from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session
from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.notification import Notification
from app.models.ticket import Ticket
from app.models.user import User
from app.schemas.notification import NotificationListResponse, NotificationOut
from app.services.notification_service import refresh_sla_notifications_for_user
from app.services.role_service import has_permission

router = APIRouter(prefix="/notifications", tags=["notifications"])


def _notification_to_out(db: Session, notification: Notification) -> dict:
    entity_ref = str(notification.entity_id) if notification.entity_id is not None else None
    if notification.entity_type == "ticket" and notification.entity_id is not None:
        ticket = db.get(Ticket, notification.entity_id)
        entity_ref = ticket.public_id if ticket else None
    return {
        "id": notification.id,
        "user_id": notification.user_id,
        "channel": notification.channel,
        "title": notification.title,
        "body": notification.body,
        "read": notification.read,
        "kind": notification.kind,
        "entity_type": notification.entity_type,
        "entity_id": entity_ref,
        "unique_key": notification.unique_key,
        "created_at": notification.created_at,
        "read_at": notification.read_at,
    }


def _ensure_can_view_notifications(db: Session, user: User) -> None:
    if has_permission(db, user, "notifications", "view") or user.role in ["requester", "analyst", "supervisor", "admin"]:
        return
    raise HTTPException(status_code=403, detail="Permiso insuficiente para ver notificaciones")


@router.get("", response_model=NotificationListResponse)
def list_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = Query(default=20, ge=1, le=100),
    unread_only: bool = False,
):
    _ensure_can_view_notifications(db, current_user)
    refresh_sla_notifications_for_user(db, current_user)
    db.commit()

    query = select(Notification).where(Notification.user_id == current_user.id)
    if unread_only:
        query = query.where(Notification.read.is_(False))
    query = query.order_by(Notification.created_at.desc()).limit(limit)
    items = db.execute(query).scalars().all()
    unread_count = db.execute(
        select(func.count(Notification.id)).where(
            Notification.user_id == current_user.id,
            Notification.read.is_(False),
        )
    ).scalar_one()
    return {"items": [_notification_to_out(db, item) for item in items], "unread_count": unread_count}


@router.get("/unread-count")
def unread_count(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _ensure_can_view_notifications(db, current_user)
    refresh_sla_notifications_for_user(db, current_user)
    db.commit()
    count = db.execute(
        select(func.count(Notification.id)).where(
            Notification.user_id == current_user.id,
            Notification.read.is_(False),
        )
    ).scalar_one()
    return {"unread_count": count}


@router.patch("/{notification_id}/read", response_model=NotificationOut)
def mark_notification_read(notification_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _ensure_can_view_notifications(db, current_user)
    notification = db.get(Notification, notification_id)
    if not notification or notification.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Notificación no encontrada")
    notification.mark_read()
    db.commit()
    db.refresh(notification)
    return _notification_to_out(db, notification)


@router.patch("/read-all")
def mark_all_read(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _ensure_can_view_notifications(db, current_user)
    db.execute(
        update(Notification)
        .where(Notification.user_id == current_user.id, Notification.read.is_(False))
        .values(read=True, read_at=func.now())
    )
    db.commit()
    return {"status": "ok"}
