from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from app.core.config import settings

UTC = timezone.utc


def app_timezone() -> ZoneInfo:
    """Zona horaria oficial de la plataforma.

    Por defecto se usa Chile continental: America/Santiago.
    Se puede cambiar con APP_TIMEZONE en el archivo .env.
    """
    return ZoneInfo(settings.APP_TIMEZONE)


def now_utc() -> datetime:
    return datetime.now(UTC)


def now_utc_naive() -> datetime:
    return now_utc().replace(tzinfo=None)


def now_app_tz() -> datetime:
    return now_utc().astimezone(app_timezone())


def now_app_naive() -> datetime:
    return now_app_tz().replace(tzinfo=None)


def as_utc_aware(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def as_utc_naive(value: datetime | None) -> datetime | None:
    aware = as_utc_aware(value)
    return aware.replace(tzinfo=None) if aware else None


def utc_naive_to_app(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return value.replace(tzinfo=UTC).astimezone(app_timezone()).replace(tzinfo=None)


def app_naive_to_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=app_timezone()).astimezone(UTC).replace(tzinfo=None)
    return value.astimezone(UTC).replace(tzinfo=None)


def frontend_local_to_utc_naive(value: datetime | None) -> datetime | None:
    """Convierte fechas ingresadas por inputs datetime-local a UTC naïve.

    Los inputs datetime-local del navegador envían fecha/hora sin zona horaria.
    Para evitar desfases, el backend las interpreta en APP_TIMEZONE.
    """
    return app_naive_to_utc(value)


def iso_utc_z(value: datetime | None) -> str | None:
    if value is None:
        return None
    return as_utc_aware(value).isoformat().replace('+00:00', 'Z')
