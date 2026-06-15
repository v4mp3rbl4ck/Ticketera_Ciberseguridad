from datetime import datetime, timedelta, time
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.timezone import now_utc_naive, utc_naive_to_app, app_naive_to_utc
from app.models.sla import SLAPolicy
from app.models.ticket import Ticket


def _parse_time(value: str) -> time:
    hour, minute = value.split(":")
    return time(hour=int(hour), minute=int(minute))


def find_sla_policy(db: Session, area: str, severity: str) -> SLAPolicy | None:
    policy = db.execute(
        select(SLAPolicy)
        .where(SLAPolicy.active.is_(True))
        .where(SLAPolicy.severity == severity)
        .where(SLAPolicy.area == area)
        .limit(1)
    ).scalar_one_or_none()
    if policy:
        return policy
    return db.execute(
        select(SLAPolicy)
        .where(SLAPolicy.active.is_(True))
        .where(SLAPolicy.severity == severity)
        .where(SLAPolicy.area.is_(None))
        .limit(1)
    ).scalar_one_or_none()


def add_business_minutes(start: datetime, minutes: int) -> datetime:
    """Suma minutos hábiles usando la zona horaria configurada.

    Los timestamps se guardan en UTC naïve en BD, pero el horario laboral
    debe calcularse en APP_TIMEZONE, por defecto America/Santiago.
    """
    business_start = _parse_time(settings.BUSINESS_HOUR_START)
    business_end = _parse_time(settings.BUSINESS_HOUR_END)
    business_days = settings.business_days_list
    local_start = utc_naive_to_app(start) or start
    current = local_start.replace(second=0, microsecond=0)
    remaining = minutes

    while remaining > 0:
        if current.weekday() not in business_days:
            current = (current + timedelta(days=1)).replace(
                hour=business_start.hour, minute=business_start.minute
            )
            continue

        start_dt = current.replace(hour=business_start.hour, minute=business_start.minute)
        end_dt = current.replace(hour=business_end.hour, minute=business_end.minute)

        if current < start_dt:
            current = start_dt
        if current >= end_dt:
            current = (current + timedelta(days=1)).replace(
                hour=business_start.hour, minute=business_start.minute
            )
            continue

        available = int((end_dt - current).total_seconds() // 60)
        consume = min(available, remaining)
        current += timedelta(minutes=consume)
        remaining -= consume

    return app_naive_to_utc(current) or current


def calculate_due_at(created_at: datetime, policy: SLAPolicy | None) -> datetime | None:
    if not policy:
        return None
    if policy.business_hours_only:
        return add_business_minutes(created_at, policy.resolution_minutes)
    return created_at + timedelta(minutes=policy.resolution_minutes)


def apply_initial_sla(db: Session, ticket: Ticket) -> None:
    policy = find_sla_policy(db, ticket.area_destino, ticket.severity)
    ticket.sla_due_at = calculate_due_at(ticket.created_at, policy)


def refresh_breach(ticket: Ticket, now: datetime | None = None) -> None:
    now = now or now_utc_naive()
    ticket.is_sla_breached = bool(
        ticket.sla_due_at
        and ticket.status not in ["Resuelto", "Cerrado"]
        and ticket.status != "En Espera"
        and now > ticket.sla_due_at
    )


def pause_sla(ticket: Ticket) -> None:
    if not ticket.sla_paused_at:
        ticket.sla_paused_at = now_utc_naive()


def resume_sla(ticket: Ticket) -> None:
    if ticket.sla_paused_at:
        now = now_utc_naive()
        paused_seconds = int((now - ticket.sla_paused_at).total_seconds())
        ticket.sla_paused_seconds += paused_seconds
        if ticket.sla_due_at:
            ticket.sla_due_at = ticket.sla_due_at + timedelta(seconds=paused_seconds)
        ticket.sla_paused_at = None


# v1.0.0.19 - SLA avanzado
TERMINAL_STATUSES = {"Resuelto", "Cerrado"}
OPEN_STATUSES = {"Nuevo", "Asignado", "En Progreso", "En Espera"}


def calculate_first_response_due_at(created_at: datetime, policy: SLAPolicy | None) -> datetime | None:
    if not policy:
        return None
    if policy.business_hours_only:
        return add_business_minutes(created_at, policy.first_response_minutes)
    return created_at + timedelta(minutes=policy.first_response_minutes)


def _safe_seconds(delta) -> int:
    return int(delta.total_seconds())


def _effective_now(ticket: Ticket, now: datetime | None = None) -> datetime:
    if ticket.status == "En Espera" and ticket.sla_paused_at:
        return ticket.sla_paused_at
    return now or now_utc_naive()


def get_sla_snapshot(db: Session, ticket: Ticket, now: datetime | None = None) -> dict:
    """Devuelve SLA calculado en tiempo real sin requerir nuevas columnas.

    Incluye estado, porcentaje consumido, segundos restantes y control de primera respuesta.
    Esto permite evolucionar el SLA sin migrar tablas ya existentes.
    """
    now = now or now_utc_naive()
    policy = find_sla_policy(db, ticket.area_destino, ticket.severity)
    due_at = ticket.sla_due_at or calculate_due_at(ticket.created_at, policy)
    first_due_at = calculate_first_response_due_at(ticket.created_at, policy)
    final_at = ticket.resolved_at or ticket.closed_at
    effective_now = _effective_now(ticket, now)
    if ticket.status in TERMINAL_STATUSES and final_at:
        effective_now = final_at

    ticket_measurement_end_at = final_at if ticket.status in TERMINAL_STATUSES and final_at else now
    ticket_age_seconds = max(0, _safe_seconds(ticket_measurement_end_at - ticket.created_at))
    sla_consumed_seconds = max(0, _safe_seconds(effective_now - ticket.created_at) - int(ticket.sla_paused_seconds or 0))

    remaining_seconds = None
    elapsed_percent = None
    state = "without_sla"
    label = "Sin SLA"
    tone = "muted"
    warning_level = 0

    if due_at:
        total_seconds = max(1, _safe_seconds(due_at - ticket.created_at))
        elapsed_seconds = sla_consumed_seconds
        remaining_seconds = _safe_seconds(due_at - effective_now)
        elapsed_percent = max(0, min(100, round((elapsed_seconds / total_seconds) * 100, 2)))

        if ticket.status in TERMINAL_STATUSES:
            if final_at and final_at <= due_at:
                state = "completed_on_time"
                label = "SLA cumplido"
                tone = "success"
            else:
                state = "completed_late"
                label = "SLA vencido al cierre"
                tone = "critical"
        elif ticket.status == "En Espera":
            state = "paused"
            label = "SLA pausado"
            tone = "warning"
        elif remaining_seconds < 0:
            state = "breached"
            label = "SLA vencido"
            tone = "critical"
            warning_level = 100
        elif elapsed_percent >= 90:
            state = "warning_90"
            label = "SLA 90% consumido"
            tone = "danger"
            warning_level = 90
        elif elapsed_percent >= 75:
            state = "warning_75"
            label = "SLA 75% consumido"
            tone = "warning"
            warning_level = 75
        else:
            state = "active"
            label = "SLA activo"
            tone = "info"

    first_response_breached = False
    first_response_elapsed_percent = None
    if first_due_at:
        response_at = ticket.first_response_at or ticket.assigned_at
        response_reference = response_at or now
        total_response_seconds = max(1, _safe_seconds(first_due_at - ticket.created_at))
        elapsed_response_seconds = max(0, _safe_seconds(response_reference - ticket.created_at))
        first_response_elapsed_percent = max(0, min(100, round((elapsed_response_seconds / total_response_seconds) * 100, 2)))
        first_response_breached = bool((response_at and response_at > first_due_at) or (not response_at and now > first_due_at))

    return {
        "sla_policy_id": policy.id if policy else None,
        "sla_policy_scope": (policy.area or "Global") if policy else None,
        "sla_business_hours_only": policy.business_hours_only if policy else None,
        "sla_pause_allowed": policy.pause_allowed if policy else None,
        "sla_first_response_due_at": first_due_at,
        "sla_first_response_breached": first_response_breached,
        "sla_first_response_elapsed_percent": first_response_elapsed_percent,
        "sla_remaining_seconds": remaining_seconds,
        "sla_elapsed_percent": elapsed_percent,
        "sla_consumed_seconds": sla_consumed_seconds,
        "sla_consumed_minutes": round(sla_consumed_seconds / 60, 2),
        "ticket_age_seconds": ticket_age_seconds,
        "ticket_age_minutes": round(ticket_age_seconds / 60, 2),
        "ticket_measurement_end_at": ticket_measurement_end_at,
        "ticket_time_is_final": bool(ticket.status in TERMINAL_STATUSES and final_at),
        "sla_paused_minutes": round((ticket.sla_paused_seconds or 0) / 60, 2),
        "sla_state": state,
        "sla_state_label": label,
        "sla_state_tone": tone,
        "sla_warning_level": warning_level,
        "sla_is_paused": ticket.status == "En Espera" and ticket.sla_paused_at is not None,
    }
