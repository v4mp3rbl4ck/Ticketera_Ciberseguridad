from __future__ import annotations

from app.models.user import User


def user_public_dict(user: User, permissions: dict | None = None) -> dict:
    return {
        "id": user.public_id,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role,
        "area": user.area,
        "is_active": user.is_active,
        "is_deleted": user.is_deleted,
        "theme_preference": user.theme_preference,
        "permissions": permissions or {},
    }
