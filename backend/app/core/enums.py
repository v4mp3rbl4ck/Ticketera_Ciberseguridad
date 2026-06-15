from enum import StrEnum


class UserRole(StrEnum):
    requester = "requester"
    analyst = "analyst"
    admin = "admin"
    supervisor = "supervisor"


class Area(StrEnum):
    cybersecurity = "Ciberseguridad"
    networking = "Networking"


class Severity(StrEnum):
    critical = "Crítica/SOS"
    high = "Alta"
    medium = "Media"
    low = "Baja"


class TicketStatus(StrEnum):
    new = "Nuevo"
    assigned = "Asignado"
    in_progress = "En Progreso"
    waiting = "En Espera"
    resolved = "Resuelto"
    closed = "Cerrado"


class TLP(StrEnum):
    clear = "TLP:CLEAR"
    green = "TLP:GREEN"
    amber = "TLP:AMBER"
    amber_strict = "TLP:AMBER+STRICT"
    red = "TLP:RED"


class CommentType(StrEnum):
    public = "public"
    internal = "internal"
    system = "system"
