from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect, text
from app.api.router import api_router
from app.core.config import settings
from app.core.database import Base, engine, SessionLocal
from app import models  # noqa: F401
from app.seed import seed
from app.core.ids import generate_public_id, assign_missing_public_ids
from app.models.user import User
from app.models.ticket import Ticket, TicketComment, TicketAttachment, TicketDynamicAnswer


def _add_column_if_missing(conn, table: str, columns: set[str], column_sql: str) -> None:
    column_name = column_sql.split()[0]
    if column_name not in columns:
        conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column_sql}"))


def ensure_runtime_columns():
    """Migraciones livianas para upgrades del MVP/RC. En producción madura usar Alembic."""
    inspector = inspect(engine)
    table_names = inspector.get_table_names()
    with engine.begin() as conn:
        if 'users' in table_names:
            user_columns = {column['name'] for column in inspector.get_columns('users')}
            if 'public_id' not in user_columns:
                conn.execute(text("ALTER TABLE users ADD COLUMN public_id VARCHAR(80)"))
            if 'theme_preference' not in user_columns:
                conn.execute(text("ALTER TABLE users ADD COLUMN theme_preference VARCHAR(20) DEFAULT 'light' NOT NULL"))
            if 'is_deleted' not in user_columns:
                conn.execute(text("ALTER TABLE users ADD COLUMN is_deleted BOOLEAN DEFAULT false NOT NULL"))
            if 'deleted_at' not in user_columns:
                conn.execute(text('ALTER TABLE users ADD COLUMN deleted_at TIMESTAMP'))
        if 'tickets' in table_names:
            ticket_columns = {column['name'] for column in inspector.get_columns('tickets')}
            if 'public_id' not in ticket_columns:
                conn.execute(text("ALTER TABLE tickets ADD COLUMN public_id VARCHAR(80)"))
        if 'ticket_comments' in table_names:
            comment_columns = {column['name'] for column in inspector.get_columns('ticket_comments')}
            if 'public_id' not in comment_columns:
                conn.execute(text("ALTER TABLE ticket_comments ADD COLUMN public_id VARCHAR(80)"))
        if 'ticket_dynamic_answers' in table_names:
            answer_columns = {column['name'] for column in inspector.get_columns('ticket_dynamic_answers')}
            if 'public_id' not in answer_columns:
                conn.execute(text("ALTER TABLE ticket_dynamic_answers ADD COLUMN public_id VARCHAR(80)"))
        if 'ticket_attachments' in table_names:
            attachment_columns = {column['name'] for column in inspector.get_columns('ticket_attachments')}
            if 'public_id' not in attachment_columns:
                conn.execute(text("ALTER TABLE ticket_attachments ADD COLUMN public_id VARCHAR(80)"))
            if 'comment_id' not in attachment_columns:
                conn.execute(text('ALTER TABLE ticket_attachments ADD COLUMN comment_id INTEGER'))
            if 'detected_mime' not in attachment_columns:
                conn.execute(text('ALTER TABLE ticket_attachments ADD COLUMN detected_mime VARCHAR(255)'))
            if 'sha256_hash' not in attachment_columns:
                conn.execute(text('ALTER TABLE ticket_attachments ADD COLUMN sha256_hash VARCHAR(128)'))
            if 'security_scan_status' not in attachment_columns:
                conn.execute(text("ALTER TABLE ticket_attachments ADD COLUMN security_scan_status VARCHAR(50) DEFAULT 'legacy' NOT NULL"))
        if 'notifications' in table_names:
            notification_columns = {column['name'] for column in inspector.get_columns('notifications')}
            if 'kind' not in notification_columns:
                conn.execute(text('ALTER TABLE notifications ADD COLUMN kind VARCHAR(80)'))
            if 'entity_type' not in notification_columns:
                conn.execute(text('ALTER TABLE notifications ADD COLUMN entity_type VARCHAR(80)'))
            if 'entity_id' not in notification_columns:
                conn.execute(text('ALTER TABLE notifications ADD COLUMN entity_id INTEGER'))
            if 'unique_key' not in notification_columns:
                conn.execute(text('ALTER TABLE notifications ADD COLUMN unique_key VARCHAR(255)'))
            if 'read_at' not in notification_columns:
                conn.execute(text('ALTER TABLE notifications ADD COLUMN read_at TIMESTAMP'))


def backfill_security_identifiers():
    """Completa identificadores públicos en datos existentes sin destruir información."""
    db = SessionLocal()
    try:
        assign_missing_public_ids(db, User, kind='user')
        assign_missing_public_ids(db, Ticket, kind='ticket')
        assign_missing_public_ids(db, TicketComment, kind='comment')
        assign_missing_public_ids(db, TicketDynamicAnswer, kind='answer')
        assign_missing_public_ids(db, TicketAttachment, kind='attachment')
        db.commit()
    finally:
        db.close()


app = FastAPI(title=settings.APP_NAME, version='1.0.0.25')
settings.upload_path.mkdir(parents=True, exist_ok=True)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=(), payment=()")
    response.headers.setdefault("Cross-Origin-Resource-Policy", "same-origin")
    if settings.ENABLE_CSP:
        response.headers.setdefault("Content-Security-Policy", settings.CONTENT_SECURITY_POLICY)
    if settings.FORCE_HTTPS:
        response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
    return response


@app.on_event('startup')
def on_startup():
    if settings.AUTO_CREATE_TABLES:
        Base.metadata.create_all(bind=engine)
        ensure_runtime_columns()
        backfill_security_identifiers()
    db = SessionLocal()
    try:
        seed(db)
    finally:
        db.close()


@app.get('/health')
def health():
    return {'status': 'ok', 'app': settings.APP_NAME, 'environment': settings.ENVIRONMENT}


app.include_router(api_router, prefix=settings.API_V1_PREFIX)
