from pydantic import BaseModel


class KPIResponse(BaseModel):
    total_tickets: int
    open_tickets: int
    closed_tickets: int
    resolved_tickets: int
    finished_tickets: int
    breached_tickets: int
    sla_warning_75: int = 0
    sla_warning_90: int = 0
    sla_paused_tickets: int = 0
    first_response_breached: int = 0
    sla_compliance_percent: float
    mtta_minutes: float | None
    mttr_minutes: float | None


class DashboardResponse(BaseModel):
    kpis: KPIResponse
    by_severity: dict[str, int]
    by_status: dict[str, int]
    by_area: dict[str, int]
    top_categories: list[dict[str, int | str]]
    top_requester_areas: list[dict[str, int | str]]
    analyst_workload: list[dict[str, int | str | None]]
    my_tickets: dict
    filters: dict[str, str | None]
