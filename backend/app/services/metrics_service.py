from datetime import datetime
from app.core.timezone import now_utc_naive, frontend_local_to_utc_naive
from collections import Counter
from sqlalchemy import select, and_
from sqlalchemy.orm import Session
from app.models.ticket import Ticket
from app.models.user import User
from app.services.sla_service import refresh_breach, get_sla_snapshot


def _minutes(delta):
    return round(delta.total_seconds() / 60, 2)


def _filter_by_dates(tickets: list[Ticket], date_from: datetime | None, date_to: datetime | None) -> list[Ticket]:
    result = []
    for ticket in tickets:
        if date_from and ticket.created_at < date_from:
            continue
        if date_to and ticket.created_at > date_to:
            continue
        result.append(ticket)
    return result


def build_dashboard(db: Session, current_user: User, date_from: datetime | None = None, date_to: datetime | None = None) -> dict:
    query = select(Ticket)
    if current_user.role == "requester":
        query = query.where(Ticket.created_by_id == current_user.id)
    elif current_user.role == "analyst" and current_user.area:
        query = query.where((Ticket.area_destino == current_user.area) | (Ticket.assigned_to_id == current_user.id))
    all_visible = list(db.execute(query).scalars().all())
    now = now_utc_naive()
    for ticket in all_visible:
        refresh_breach(ticket, now)
    db.flush()

    tickets = _filter_by_dates(all_visible, date_from, date_to)
    total = len(tickets)
    resolved_only = len([t for t in tickets if t.status == "Resuelto"])
    closed_only = len([t for t in tickets if t.status == "Cerrado"])
    finished = len([t for t in tickets if t.status in ["Resuelto", "Cerrado"]])
    open_tickets = len([t for t in tickets if t.status not in ["Resuelto", "Cerrado"]])
    sla_snapshots = [get_sla_snapshot(db, t, now) for t in tickets]
    breached = len([t for t in tickets if t.is_sla_breached])
    sla_warning_75 = len([s for s in sla_snapshots if s.get("sla_state") == "warning_75"])
    sla_warning_90 = len([s for s in sla_snapshots if s.get("sla_state") == "warning_90"])
    sla_paused = len([s for s in sla_snapshots if s.get("sla_state") == "paused"])
    first_response_breached = len([s for s in sla_snapshots if s.get("sla_first_response_breached")])
    resolved = [t for t in tickets if t.resolved_at]
    resolved_with_sla = [t for t in resolved if t.sla_due_at]
    resolved_ok = [t for t in resolved_with_sla if t.resolved_at and t.resolved_at <= t.sla_due_at]
    sla_compliance = round((len(resolved_ok) / len(resolved_with_sla) * 100), 2) if resolved_with_sla else 100.0

    mtta_values = []
    mttr_values = []
    for t in tickets:
        first_attention = t.first_response_at or t.assigned_at
        if first_attention:
            mtta_values.append(_minutes(first_attention - t.created_at))
        if t.resolved_at:
            mttr_values.append(_minutes(t.resolved_at - t.created_at) - (t.sla_paused_seconds / 60))

    by_severity = Counter(t.severity for t in tickets)
    by_status = Counter(t.status for t in tickets)
    by_area = Counter(t.area_destino for t in tickets)
    by_category = Counter(t.category for t in tickets)
    by_requester_area = Counter(t.project_area for t in tickets if t.project_area)

    analysts = list(db.execute(select(User).where(User.is_deleted.is_(False), User.role.in_(["analyst", "admin", "supervisor"]))).scalars().all())
    workload = []
    for analyst in analysts:
        active = len([t for t in tickets if t.assigned_to_id == analyst.id and t.status not in ["Resuelto", "Cerrado"]])
        solved = len([t for t in tickets if t.assigned_to_id == analyst.id and t.status in ["Resuelto", "Cerrado"]])
        workload.append({"analyst_id": analyst.id, "analyst": analyst.full_name, "active": active, "resolved": solved})

    if current_user.role == "requester":
        my_base = [t for t in all_visible if t.created_by_id == current_user.id]
    else:
        my_base = [t for t in all_visible if t.assigned_to_id == current_user.id]
    my_tickets = {
        "total": len(my_base),
        "pending": len([t for t in my_base if t.status in ["Nuevo", "Asignado"]]),
        "in_review": len([t for t in my_base if t.status in ["En Progreso", "En Espera"]]),
        "completed": len([t for t in my_base if t.status in ["Resuelto", "Cerrado"]]),
        "by_status": dict(Counter(t.status for t in my_base)),
    }

    return {
        "kpis": {
            "total_tickets": total,
            "open_tickets": open_tickets,
            "closed_tickets": closed_only,
            "resolved_tickets": resolved_only,
            "finished_tickets": finished,
            "breached_tickets": breached,
            "sla_warning_75": sla_warning_75,
            "sla_warning_90": sla_warning_90,
            "sla_paused_tickets": sla_paused,
            "first_response_breached": first_response_breached,
            "sla_compliance_percent": sla_compliance,
            "mtta_minutes": round(sum(mtta_values) / len(mtta_values), 2) if mtta_values else None,
            "mttr_minutes": round(sum(mttr_values) / len(mttr_values), 2) if mttr_values else None,
        },
        "by_severity": dict(by_severity),
        "by_status": dict(by_status),
        "by_area": dict(by_area),
        "top_categories": [{"category": c, "count": n} for c, n in by_category.most_common(10)],
        "top_requester_areas": [{"area": c, "count": n} for c, n in by_requester_area.most_common(10)],
        "analyst_workload": workload,
        "my_tickets": my_tickets,
        "filters": {
            "date_from": date_from.isoformat() if date_from else None,
            "date_to": date_to.isoformat() if date_to else None,
        },
    }
