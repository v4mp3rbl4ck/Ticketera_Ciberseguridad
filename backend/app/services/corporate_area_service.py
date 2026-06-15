from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.corporate_area import CorporateArea


DEFAULT_CORPORATE_AREAS = [
    "AREA LEGAL",
    "AUDIO",
    "CABLE",
    "CALIDAD DE VIDA LABORAL",
    "CAPACITACION",
    "COMUNICACIONES CORPORATIVAS",
    "CONTABILIDAD",
    "CONTENIDOS MULTIPLATAFORMAS",
    "CONTRALORIA",
    "DESARROLLO MULTIPLATAFORMA",
    "DIR PROCESOS CREATIVOS Y PROG.",
    "DIRECCION DE GESTION",
    "DIRECCION EJECUTIVA",
    "EQUIPOS DE PRODUCCION FIJO",
    "FINANZAS",
    "GERENCIA DE INGENIERIA",
    "GERENCIA DE MARKETING",
    "GERENCIA DE PERSONAS",
    "GERENCIA DE PRODUCCION",
    "ILUMINACION",
    "INFORMATICA",
    "INFRAESTRUCTURA Y SERVICIOS",
    "INVESTIGACION Y AUDIENCIAS",
    "MANTENCION DE RED",
    "MEDIOS DIGITALES",
    "NUEVAS SEÑALES",
    "PERSONAL Y REMUNERACIONES",
    "PLANIFICACION Y GESTION",
    "PRENSA",
    "PREVENCION DE RIESGOS",
    "PRODUCTORES EJECUTIVOS",
    "REGIONAL CONCEPCION",
    "REGIONAL VALPARAISO",
    "SERVICIOS ESCENOGRAFICOS",
    "SOPORTE ELECTRICO",
    "SOPORTE TECNICO",
    "SUPERVISION Y CONTROL TECNICO",
    "TRANSMISION",
    "TRANSPORTE Y MOVILIZACION",
    "VENTAS NEGOCIOS",
]


def seed_corporate_areas(db: Session) -> None:
    if db.execute(select(CorporateArea)).first():
        return
    db.add_all([CorporateArea(name=name, is_active=True) for name in DEFAULT_CORPORATE_AREAS])


def list_active_corporate_area_names(db: Session) -> list[str]:
    rows = db.execute(
        select(CorporateArea)
        .where(CorporateArea.is_active.is_(True))
        .order_by(CorporateArea.name)
    ).scalars().all()
    return [row.name for row in rows]
