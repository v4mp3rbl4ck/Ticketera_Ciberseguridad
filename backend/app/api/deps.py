from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select, or_
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db
from app.core.security import decode_token
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_PREFIX}/auth/login")


def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)) -> User:
    try:
        payload = decode_token(token)
        subject = str(payload.get("sub") or "")
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No autenticado") from exc

    user = None
    if subject:
        user = db.execute(select(User).where(User.public_id == subject)).scalar_one_or_none()
        if not user and subject.isdigit():
            # Compatibilidad temporal con tokens emitidos antes de v1.0.0.24.
            user = db.get(User, int(subject))
    if not user or not user.is_active or user.is_deleted:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario inválido o inactivo")
    return user


def require_roles(*roles: str):
    def checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permiso insuficiente")
        return current_user
    return checker


def get_analysts_by_area(db: Session, area: str) -> list[User]:
    return list(
        db.execute(
            select(User)
            .where(User.is_active.is_(True))
            .where(User.is_deleted.is_(False))
            .where(User.role.in_(["analyst", "admin", "supervisor"]))
            .where((User.area == area) | (User.area.is_(None)))
        ).scalars().all()
    )


from app.services.role_service import has_permission


def require_permission(module_key: str, action: str = "view"):
    def checker(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> User:
        if has_permission(db, current_user, module_key, action):
            return current_user
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permiso insuficiente para este módulo")
    return checker
