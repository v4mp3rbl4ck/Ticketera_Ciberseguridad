from sqlalchemy import select, delete, inspect, text
from sqlalchemy.orm import Session
from app.core.security import get_password_hash
from app.models.user import User
from app.models.category import Category
from app.models.sla import SLAPolicy
from app.models.required_question import RequiredQuestion
from app.services.ticket_catalog_service import CATALOG, get_questions
from app.services.corporate_area_service import seed_corporate_areas
from app.services.required_question_service import make_question_key
from app.services.role_service import seed_roles

CATALOG_VERSION_MARKER = "v3_dynamic_severity_catalog"


def _ensure_category_schema(db: Session) -> None:
    """Compatibilidad para bases SQLite creadas por versiones anteriores del MVP."""
    inspector = inspect(db.bind)
    if not inspector.has_table("categories"):
        return
    columns = {column["name"] for column in inspector.get_columns("categories")}
    if "severity" not in columns:
        db.execute(text("ALTER TABLE categories ADD COLUMN severity VARCHAR(50) DEFAULT 'Media' NOT NULL"))
        db.commit()


def _ensure_user_schema(db: Session) -> None:
    """Compatibilidad para bases SQLite creadas por versiones anteriores."""
    inspector = inspect(db.bind)
    if not inspector.has_table("users"):
        return
    columns = {column["name"] for column in inspector.get_columns("users")}
    if "is_deleted" not in columns:
        db.execute(text("ALTER TABLE users ADD COLUMN is_deleted BOOLEAN DEFAULT 0 NOT NULL"))
    if "deleted_at" not in columns:
        db.execute(text("ALTER TABLE users ADD COLUMN deleted_at DATETIME"))
    db.commit()


def _seed_users(db: Session) -> None:
    if not db.execute(select(User).where(User.email == "admin@ticketera.cl")).scalar_one_or_none():
        users = [
            User(email="admin@ticketera.cl", full_name="Administrador", hashed_password=get_password_hash("Admin123!"), role="admin", area=None),
            User(email="analyst.cyber@ticketera.cl", full_name="Analista Ciberseguridad", hashed_password=get_password_hash("Analyst123!"), role="analyst", area="Ciberseguridad"),
            User(email="analyst.net@ticketera.cl", full_name="Analista Networking", hashed_password=get_password_hash("Analyst123!"), role="analyst", area="Networking"),
            User(email="user@ticketera.cl", full_name="Usuario Solicitante", hashed_password=get_password_hash("User123!"), role="requester", area=None),
        ]
        db.add_all(users)


def _seed_categories(db: Session) -> None:
    """Carga inicial del catálogo dinámico de casos de uso.

    En versiones anteriores todos los casos de uso seeded usaban el mismo valor
    en description como marcador de versión. Por eso no se debe usar
    scalar_one_or_none(), porque una base existente tendrá múltiples filas con
    ese marcador y SQLAlchemy lanzará MultipleResultsFound durante el startup.

    La comprobación debe ser de existencia: basta con encontrar una fila.
    Esto permite actualizar desde versiones anteriores sin borrar la base de
    datos, tickets ni evidencias.
    """
    marker_exists = db.execute(
        select(Category.id)
        .where(Category.description == CATALOG_VERSION_MARKER)
        .limit(1)
    ).first()

    if marker_exists:
        return

    # El catálogo v3 reemplaza el menú gigante por opciones dependientes de área + severidad.
    # Ticket.category es texto y no FK, por lo que es seguro refrescar esta tabla maestra
    # solo cuando el marcador no existe.
    db.execute(delete(Category))

    rows: list[Category] = []
    for area, severities in CATALOG.items():
        for severity, item in severities.items():
            for use_case in item.use_cases:
                rows.append(Category(area=area, severity=severity, name=use_case, description=CATALOG_VERSION_MARKER))
    db.add_all(rows)


def _seed_sla(db: Session) -> None:
    if not db.execute(select(SLAPolicy)).first():
        db.add_all([
            SLAPolicy(area=None, severity="Alta", first_response_minutes=30, resolution_minutes=480, business_hours_only=False),
            SLAPolicy(area=None, severity="Media", first_response_minutes=240, resolution_minutes=1440, business_hours_only=True),
            SLAPolicy(area=None, severity="Baja", first_response_minutes=480, resolution_minutes=3000, business_hours_only=True),
        ])


def _seed_required_questions(db: Session) -> None:
    if db.execute(select(RequiredQuestion)).first():
        return
    rows: list[RequiredQuestion] = []
    for area, severities in CATALOG.items():
        for severity in severities.keys():
            for index, (key, text_value) in enumerate(get_questions(area, severity), start=1):
                rows.append(RequiredQuestion(
                    area=area,
                    severity=severity,
                    category="*",
                    question_key=key or make_question_key(text_value),
                    question_text=text_value,
                    required=True,
                    sort_order=index,
                    is_active=True,
                ))
    db.add_all(rows)


def seed(db: Session) -> None:
    _ensure_category_schema(db)
    _ensure_user_schema(db)
    seed_roles(db)
    _seed_users(db)
    _seed_categories(db)
    _seed_sla(db)
    _seed_required_questions(db)
    seed_corporate_areas(db)
    db.commit()
