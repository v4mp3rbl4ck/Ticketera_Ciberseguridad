from fastapi import APIRouter
from app.api.routes import auth, tickets, sos, admin, metrics, reports, notifications

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(tickets.router)
api_router.include_router(sos.router)
api_router.include_router(admin.router)
api_router.include_router(metrics.router)
api_router.include_router(reports.router)
api_router.include_router(notifications.router)
