from datetime import datetime, timedelta, timezone
from typing import Any
import re
from jose import jwt, JWTError
from passlib.context import CryptContext
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)



def validate_password_policy(password: str, email: str | None = None) -> None:
    """Valida la política mínima de contraseñas para cuentas locales."""
    errors: list[str] = []
    min_length = settings.PASSWORD_MIN_LENGTH
    if len(password or "") < min_length:
        errors.append(f"mínimo {min_length} caracteres")
    if settings.PASSWORD_REQUIRE_UPPERCASE and not re.search(r"[A-ZÁÉÍÓÚÑ]", password or ""):
        errors.append("al menos una mayúscula")
    if settings.PASSWORD_REQUIRE_LOWERCASE and not re.search(r"[a-záéíóúñ]", password or ""):
        errors.append("al menos una minúscula")
    if settings.PASSWORD_REQUIRE_NUMBER and not re.search(r"\d", password or ""):
        errors.append("al menos un número")
    if settings.PASSWORD_REQUIRE_SPECIAL and not re.search(r"[^A-Za-z0-9ÁÉÍÓÚÑáéíóúñ]", password or ""):
        errors.append("al menos un carácter especial")
    if email:
        local_part = email.split("@", 1)[0].lower()
        if local_part and len(local_part) >= 4 and local_part in (password or "").lower():
            errors.append("no debe contener el usuario/correo")
    if errors:
        raise ValueError("La contraseña debe cumplir: " + ", ".join(errors))

def create_access_token(subject: str, extra_claims: dict[str, Any] | None = None) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode: dict[str, Any] = {"sub": subject, "exp": expire}
    if extra_claims:
        to_encode.update(extra_claims)
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError as exc:
        raise ValueError("Token inválido") from exc
