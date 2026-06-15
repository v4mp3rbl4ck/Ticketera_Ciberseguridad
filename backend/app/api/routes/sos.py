from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.api.deps import get_current_user, require_roles
from app.core.database import get_db
from app.models.sos import SOSEvent
from app.models.user import User
from app.schemas.sos import SOSEventCreate, SOSEventOut
from app.services.audit_service import write_audit

router = APIRouter(prefix="/sos", tags=["sos"])


@router.post("", response_model=SOSEventOut)
def create_sos(payload: SOSEventCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    event = SOSEvent(created_by_id=current_user.id, **payload.model_dump())
    db.add(event)
    db.flush()
    write_audit(db, actor=current_user, entity_type="sos_event", entity_id=event.id, action="create", new_value=event.affected_service)
    db.commit()
    db.refresh(event)
    return event


@router.get("", response_model=list[SOSEventOut])
def list_sos(db: Session = Depends(get_db), current_user: User = Depends(require_roles("analyst", "admin", "supervisor"))):
    return list(db.execute(select(SOSEvent).order_by(SOSEvent.created_at.desc())).scalars().all())
