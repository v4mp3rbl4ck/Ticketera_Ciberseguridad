import hashlib
import json
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.audit import AuditLog
from app.models.user import User


def _payload_hash(payload: dict) -> str:
    raw = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def write_audit(
    db: Session,
    *,
    actor: User | None,
    entity_type: str,
    entity_id: str | int,
    action: str,
    old_value: str | None = None,
    new_value: str | None = None,
    source_ip: str | None = None,
    user_agent: str | None = None,
) -> AuditLog:
    last = db.execute(select(AuditLog).order_by(AuditLog.id.desc()).limit(1)).scalar_one_or_none()
    previous_hash = last.current_hash if last else None
    payload = {
        "actor_user_id": actor.id if actor else None,
        "actor_role": actor.role if actor else None,
        "entity_type": entity_type,
        "entity_id": str(entity_id),
        "action": action,
        "old_value": old_value,
        "new_value": new_value,
        "previous_hash": previous_hash,
    }
    audit = AuditLog(
        actor_user_id=actor.id if actor else None,
        actor_role=actor.role if actor else None,
        entity_type=entity_type,
        entity_id=str(entity_id),
        action=action,
        old_value=old_value,
        new_value=new_value,
        source_ip=source_ip,
        user_agent=user_agent,
        previous_hash=previous_hash,
        current_hash=_payload_hash(payload),
    )
    db.add(audit)
    db.flush()
    return audit
