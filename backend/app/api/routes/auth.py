from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import verify_password, create_access_token, get_password_hash, validate_password_policy
from app.models.user import User
from app.schemas.auth import LoginResponse, UserOut, PasswordChange, ProfileUpdate
from app.api.deps import get_current_user
from app.services.role_service import get_user_permissions
from app.services.output_service import user_public_dict
from app.services.audit_service import write_audit
from app.core.config import settings
from time import time

router = APIRouter(prefix="/auth", tags=["auth"])

_login_attempts: dict[str, list[float]] = {}


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _login_key(request: Request, username: str) -> str:
    return f"{_client_ip(request)}:{username.lower().strip()}"


def _check_login_rate_limit(key: str) -> None:
    now = time()
    window = settings.LOGIN_RATE_LIMIT_WINDOW_SECONDS
    attempts = [item for item in _login_attempts.get(key, []) if now - item < window]
    _login_attempts[key] = attempts
    if len(attempts) >= settings.LOGIN_RATE_LIMIT_ATTEMPTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Demasiados intentos fallidos. Intenta nuevamente en {max(1, window // 60)} minutos.",
        )


def _register_failed_login(key: str) -> None:
    now = time()
    window = settings.LOGIN_RATE_LIMIT_WINDOW_SECONDS
    attempts = [item for item in _login_attempts.get(key, []) if now - item < window]
    attempts.append(now)
    _login_attempts[key] = attempts


def _clear_failed_login(key: str) -> None:
    _login_attempts.pop(key, None)


def _user_out(db: Session, user: User) -> UserOut:
    return UserOut(**user_public_dict(user, get_user_permissions(db, user)))


@router.post("/login", response_model=LoginResponse)
def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    key = _login_key(request, form_data.username)
    _check_login_rate_limit(key)
    user = db.execute(select(User).where(User.email == form_data.username)).scalar_one_or_none()
    if not user or user.is_deleted or not verify_password(form_data.password, user.hashed_password):
        _register_failed_login(key)
        # Auditoría de autenticación fallida sin exponer si el usuario existe.
        if user:
            write_audit(db, actor=user, entity_type="auth", entity_id=user.public_id, action="login_failed", new_value=_client_ip(request))
            db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales inválidas")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Usuario inactivo")
    _clear_failed_login(key)
    write_audit(db, actor=user, entity_type="auth", entity_id=user.public_id, action="login_success", new_value=_client_ip(request))
    db.commit()
    token = create_access_token(subject=user.public_id, extra_claims={"role": user.role})
    return LoginResponse(access_token=token, user=_user_out(db, user))


@router.get("/me", response_model=UserOut)
def me(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return _user_out(db, current_user)


@router.patch("/profile", response_model=UserOut)
def update_profile(payload: ProfileUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if payload.full_name:
        current_user.full_name = payload.full_name
    if payload.theme_preference in ["light", "dark"]:
        current_user.theme_preference = payload.theme_preference
    write_audit(db, actor=current_user, entity_type="user", entity_id=current_user.public_id, action="profile_update")
    db.commit()
    db.refresh(current_user)
    return _user_out(db, current_user)


@router.post("/change-password")
def change_password(payload: PasswordChange, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not verify_password(payload.current_password, current_user.hashed_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Contraseña actual incorrecta")
    try:
        validate_password_policy(payload.new_password, current_user.email)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    current_user.hashed_password = get_password_hash(payload.new_password)
    write_audit(db, actor=current_user, entity_type="user", entity_id=current_user.public_id, action="password_change")
    db.commit()
    return {"ok": True}
