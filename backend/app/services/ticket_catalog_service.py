from __future__ import annotations

from dataclasses import dataclass


AREAS = ["Ciberseguridad", "Networking"]
SEVERITIES = ["Crítica/SOS", "Alta", "Media", "Baja"]


@dataclass(frozen=True)
class SeverityCatalog:
    channel: str
    sla_mode: str
    description: str
    use_cases: list[str]
    questions: list[tuple[str, str]]


def _question(prefix: str, idx: int, text: str) -> tuple[str, str]:
    return (f"{prefix}_{idx:02d}", text)


SOS_QUESTIONS = [
    _question("sos", 1, "Registrar fecha y hora de la llamada telefónica realizada a jefatura."),
    _question("sos", 2, "Indicar a qué jefatura se reportó el estado del incidente."),
    _question("sos", 3, "Describir cuál es la afectación general y qué áreas, usuarios o servicios están impactados."),
    _question("sos", 4, "Indicar qué plan, política o procedimiento de respuesta fue activado."),
]

CATALOG: dict[str, dict[str, SeverityCatalog]] = {
    "Ciberseguridad": {
        "Crítica/SOS": SeverityCatalog(
            channel="Solo llamada inicial. Registro posterior obligatorio en módulo SOS.",
            sla_mode="Gestión 24/7 según plan de respuesta a incidentes.",
            description="Pérdida de continuidad operativa general, caída de sistemas de áreas completas o indisponibilidad de servicios generales.",
            use_cases=[
                "Pérdida de continuidad operativa general",
                "Caída de sistema que afecte áreas completas",
                "Indisponibilidad de servicios generales",
            ],
            questions=SOS_QUESTIONS,
        ),
        "Alta": SeverityCatalog(
            channel="Correo/Ticket con atención urgente dentro y fuera de horario laboral.",
            sla_mode="SLA de urgencia, notificación a turno y escalamiento si corresponde.",
            description="Incidentes de seguridad con impacto alto o riesgo operacional relevante.",
            use_cases=[
                "Análisis de correos sospechosos o phishing masivo",
                "Revisión de malware en equipos",
                "Contención de incidentes en endpoints o servidores",
                "Escalamiento de eventos de seguridad detectados por soporte",
                "Revisión de logs de eventos sospechosos",
                "Alertas por intentos de fuerza bruta",
            ],
            questions=[
                _question("cyber_high", 1, "¿Cuál es el incidente exacto y cómo fue detectado?"),
                _question("cyber_high", 2, "¿Qué usuario, equipo, servidor o cuenta está involucrado?"),
                _question("cyber_high", 3, "¿Desde cuándo ocurre y cuál fue la fecha/hora del primer evento?"),
                _question("cyber_high", 4, "¿Qué evidencia tienen disponible? Correo, logs, capturas, IP, hostname o alertas."),
                _question("cyber_high", 5, "¿Cuál es el impacto actual en la operación, usuarios o servicios?"),
            ],
        ),
        "Media": SeverityCatalog(
            channel="Correo/Ticket en horario laboral.",
            sla_mode="Atención prioritaria en horario laboral.",
            description="Solicitudes de revisión, validación o análisis sin caída general del servicio.",
            use_cases=[
                "Análisis de correo sospechoso o phishing de usuario único",
                "Validación de antivirus o EDR",
                "Revisión de vulnerabilidades en PCs, laptops o servidores",
                "Análisis y desbloqueo de software no autorizado",
                "Habilitación de dispositivos USB, correo o navegación",
                "Evaluación de riesgo de nuevas herramientas",
                "Aprobación de excepciones de seguridad",
            ],
            questions=[
                _question("cyber_medium", 1, "¿Cuál es el incidente exacto y cómo fue detectado?"),
                _question("cyber_medium", 2, "¿Qué usuario, equipo, servidor o cuenta está involucrado?"),
                _question("cyber_medium", 3, "¿Cuál es el objetivo de la solicitud?"),
                _question("cyber_medium", 4, "¿Desde cuándo ocurre y cuál fue la fecha/hora del primer evento?"),
                _question("cyber_medium", 5, "¿Qué evidencia tienen disponible? Correo, logs, capturas, IP, hostname o alertas."),
            ],
        ),
        "Baja": SeverityCatalog(
            channel="Correo/Ticket en horario laboral.",
            sla_mode="Planificación en horario laboral.",
            description="Solicitudes planificadas, documentación, capacitación o seguimiento sin urgencia operacional.",
            use_cases=[
                "Capacitación a soporte para reconocer incidentes",
                "Instructivos para identificar phishing",
                "Buenas prácticas de atención segura al usuario",
                "Simulacros o ejercicios de respuesta",
                "Reportes sobre hallazgos y remediaciones",
                "Revisión de seguridad antes de implementar cambios técnicos",
                "Seguimiento documental de planes de acción ya aprobados",
            ],
            questions=[
                _question("cyber_low", 1, "¿Cuál es el incidente exacto o necesidad que debe revisarse?"),
                _question("cyber_low", 2, "¿Qué usuario, equipo, servidor o cuenta está involucrado?"),
                _question("cyber_low", 3, "¿Cuál es el objetivo de la solicitud?"),
                _question("cyber_low", 4, "¿Desde cuándo ocurre y cuál fue la fecha/hora del primer evento, si aplica?"),
                _question("cyber_low", 5, "¿Qué evidencia tienen disponible? Correo, logs, capturas, IP, hostname o alertas."),
            ],
        ),
    },
    "Networking": {
        "Crítica/SOS": SeverityCatalog(
            channel="Solo llamada inicial. Registro posterior obligatorio en módulo SOS.",
            sla_mode="Gestión 24/7 según plan de continuidad/respuesta.",
            description="Pérdida de continuidad operativa general, caída de sistemas de áreas completas o indisponibilidad de servicios generales.",
            use_cases=[
                "Pérdida de continuidad operativa general",
                "Caída de sistemas que afecte áreas completas",
                "Indisponibilidad de servicios generales",
            ],
            questions=SOS_QUESTIONS,
        ),
        "Alta": SeverityCatalog(
            channel="Correo/Ticket con atención urgente dentro y fuera de horario laboral.",
            sla_mode="SLA de urgencia, notificación a turno y escalamiento si corresponde.",
            description="Fallas de red que afectan operación crítica o a múltiples usuarios, áreas o servicios productivos.",
            use_cases=[
                "Lentitud severa que afecta operación, transmisión o servicios críticos",
                "Falla de conectividad en estudio, master o data center",
                "Pérdida de conectividad hacia sistemas de emisión, producción o streaming",
                "Incidente de firewall que bloquea servicios críticos",
                "Saturación de ancho de banda que afecta operación general",
                "Falla de red que impacta a múltiples usuarios o áreas",
            ],
            questions=[
                _question("net_high", 1, "¿Cuál es el área, usuario o servicio afectado?"),
                _question("net_high", 2, "¿Cuántos usuarios o equipos están afectados?"),
                _question("net_high", 3, "¿Desde cuándo inició la falla?"),
                _question("net_high", 4, "¿La afectación es total, parcial, constante o intermitente?"),
                _question("net_high", 5, "¿Qué evidencia tienen? Capturas, alertas, fotos, logs o mensajes de error."),
                _question("net_high", 6, "¿La falla ocurre por cable, WiFi o ambos?"),
                _question("net_high", 7, "¿Ya se validó si otros puntos de red presentan el mismo problema?"),
            ],
        ),
        "Media": SeverityCatalog(
            channel="Correo/Ticket en horario laboral.",
            sla_mode="Atención prioritaria en horario laboral.",
            description="Soporte, configuración o revisión de red con impacto acotado o no crítico.",
            use_cases=[
                "Configuración o soporte de VPN para usuario o área",
                "Acceso a internet para un equipo específico",
                "Lentitud parcial en una VLAN, segmento o área no crítica",
                "Configuración o modificación de reglas de firewall no críticas",
                "Apertura o cierre de puertos específicos",
                "Acceso de un host específico a un servicio interno o externo",
                "Problemas de conectividad inalámbrica en zonas puntuales",
                "Cambio de configuración en switches, routers o access points",
                "Revisión de conectividad entre sedes sin impacto total",
            ],
            questions=[
                _question("net_medium", 1, "¿Qué usuario, equipo o grupo reducido está afectado?"),
                _question("net_medium", 2, "¿El problema ocurre por cable o WiFi?"),
                _question("net_medium", 3, "Si es WiFi, ¿la red WiFi es la correcta?"),
                _question("net_medium", 4, "Si es cable, ¿se probó con otro cable de red?"),
                _question("net_medium", 5, "¿Se probó con otro punto de red?"),
                _question("net_medium", 6, "¿El equipo tiene dirección IP asignada?"),
                _question("net_medium", 7, "¿Qué servicio no funciona: internet, VPN, interno, correo, aplicación?"),
                _question("net_medium", 8, "¿La lentitud es constante o intermitente?"),
                _question("net_medium", 9, "¿Qué velocidad obtiene en una prueba de velocidad?"),
                _question("net_medium", 10, "¿Hay evidencia del error o comportamiento presentado?"),
            ],
        ),
        "Baja": SeverityCatalog(
            channel="Correo/Ticket en horario laboral.",
            sla_mode="Planificación en horario laboral.",
            description="Cambios planificados, desbloqueos, reportes, validaciones o apoyo preventivo.",
            use_cases=[
                "Desbloqueo de página web",
                "Creación o modificación planificada de reglas en firewall",
                "Configuración planificada de puertos de red",
                "Validación de inventario de equipos de red",
                "Solicitud de reportes de disponibilidad o tráfico",
                "Apoyo en planificación de cambios de red",
                "Revisión preventiva de configuración de red",
            ],
            questions=[
                _question("net_low", 1, "¿Qué usuario o área solicita el cambio?"),
                _question("net_low", 2, "¿Cuál es la URL exacta que necesita acceder?"),
                _question("net_low", 3, "¿Qué mensaje de bloqueo aparece? Adjuntar evidencia."),
                _question("net_low", 4, "¿Se intentó acceder desde otro equipo o red?"),
                _question("net_low", 5, "¿Qué IP, host, puerto o aplicación requiere acceso?"),
                _question("net_low", 6, "¿El acceso será temporal o permanente?"),
                _question("net_low", 7, "¿Quién aprueba la solicitud?"),
                _question("net_low", 8, "¿En qué fecha u horario se requiere aplicar el cambio?"),
                _question("net_low", 9, "¿Existe documentación, ticket o antecedente relacionado?"),
            ],
        ),
    },
}


def get_area_catalog(area: str) -> dict[str, SeverityCatalog]:
    return CATALOG.get(area, {})


def get_severity_catalog(area: str, severity: str) -> SeverityCatalog | None:
    return CATALOG.get(area, {}).get(severity)


def get_use_cases(area: str, severity: str) -> list[str]:
    catalog = get_severity_catalog(area, severity)
    return catalog.use_cases if catalog else []


def get_questions(area: str, severity: str) -> list[tuple[str, str]]:
    catalog = get_severity_catalog(area, severity)
    return catalog.questions if catalog else []


def export_catalog() -> dict:
    return {
        area: {
            severity: {
                "channel": item.channel,
                "sla_mode": item.sla_mode,
                "description": item.description,
                "use_cases": item.use_cases,
                "questions": [{"key": key, "text": text, "required": True} for key, text in item.questions],
            }
            for severity, item in severities.items()
        }
        for area, severities in CATALOG.items()
    }
