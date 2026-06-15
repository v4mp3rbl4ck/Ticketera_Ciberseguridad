from __future__ import annotations

import secrets
import string
from sqlalchemy import select
from sqlalchemy.orm import Session

_ALPHABET = "23456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
_PREFIXES = {
    "user": "usr",
    "ticket": "tkt",
    "comment": "com",
    "attachment": "att",
    "answer": "ans",
    "security_event": "sec",
}


def generate_public_id(kind: str = "obj", length: int = 22) -> str:
    """Genera identificadores públicos no secuenciales para evitar enumeración/IDOR simple."""
    prefix = _PREFIXES.get(kind, kind[:3].lower() if kind else "obj")
    token = "".join(secrets.choice(_ALPHABET) for _ in range(length))
    return f"{prefix}_{token}"


def assign_missing_public_ids(db: Session, model, *, kind: str, batch_size: int = 500) -> int:
    """Asigna public_id a registros existentes durante upgrades livianos del MVP.

    Protege el arranque ante modelos heredados o upgrades parciales: si un modelo no
    expone public_id en SQLAlchemy, se omite en vez de detener el backend.
    """
    if not hasattr(model, "public_id"):
        return 0
    updated = 0
    while True:
        rows = db.execute(
            select(model).where((model.public_id.is_(None)) | (model.public_id == "")).limit(batch_size)
        ).scalars().all()
        if not rows:
            break
        for row in rows:
            row.public_id = generate_public_id(kind)
            updated += 1
        db.flush()
    return updated
