from datetime import datetime
from app.core.timezone import frontend_local_to_utc_naive
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.metrics import DashboardResponse
from app.services.metrics_service import build_dashboard

router = APIRouter(prefix="/metrics", tags=["metrics"])


def _parse_date(value: str | None) -> datetime | None:
    if not value:
        return None
    return frontend_local_to_utc_naive(datetime.fromisoformat(value))


@router.get("/dashboard", response_model=DashboardResponse)
def dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    date_from: str | None = Query(default=None),
    date_to: str | None = Query(default=None),
):
    return build_dashboard(db, current_user, _parse_date(date_from), _parse_date(date_to))
