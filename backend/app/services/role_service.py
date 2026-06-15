from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload
from app.models.role import Role, RolePermission
from app.models.user import User

ROLE_MODULES = [
    {"key": "dashboard", "label": "Dashboard", "description": "Métricas operativas y personales", "group": "Operación"},
    {"key": "tickets", "label": "Tickets", "description": "Listado, detalle, gestión, adjuntos y comentarios", "group": "Operación"},
    {"key": "kanban", "label": "Kanban Operativo", "description": "Tablero operativo de tickets por estado", "group": "Operación"},
    {"key": "new_ticket", "label": "Nuevo Ticket", "description": "Creación de tickets de solicitud", "group": "Operación"},
    {"key": "sos", "label": "Registro SOS", "description": "Registro posterior de incidentes críticos", "group": "Operación"},
    {"key": "profile", "label": "Perfil", "description": "Perfil personal, contraseña y dashboard de usuario", "group": "Cuenta"},
    {"key": "notifications", "label": "Notificaciones", "description": "Centro interno de notificaciones y alertas", "group": "Cuenta"},
    {"key": "reports", "label": "Reportes", "description": "Exportaciones PDF, Excel y CSV", "group": "Operación"},
    {"key": "admin_users", "label": "Usuarios", "description": "Administración de usuarios y reset de contraseñas", "group": "Administración"},
    {"key": "admin_roles", "label": "Roles", "description": "Roles personalizados y permisos por módulo", "group": "Administración"},
    {"key": "admin_use_cases", "label": "Casos de Uso", "description": "Catálogo dinámico de casos de uso", "group": "Administración"},
    {"key": "admin_questions", "label": "Preguntas Requeridas", "description": "Preguntas por área, severidad y caso de uso", "group": "Administración"},
    {"key": "admin_sla", "label": "SLA", "description": "Políticas SLA por severidad", "group": "Administración"},
    {"key": "admin_corporate_areas", "label": "Áreas Corporativas", "description": "Áreas solicitantes del negocio", "group": "Administración"},
    {"key": "admin_audit", "label": "Auditoría", "description": "Log de auditoría e integridad", "group": "Administración"},
]

MODULE_KEYS = [item["key"] for item in ROLE_MODULES]


def _empty_permissions() -> dict[str, dict[str, bool]]:
    return {key: {"view": False, "create": False, "edit": False, "delete": False} for key in MODULE_KEYS}


def _set(perms: dict, module_key: str, view=False, create=False, edit=False, delete=False):
    perms[module_key] = {
        "view": bool(view or create or edit or delete),
        "create": bool(create),
        "edit": bool(edit),
        "delete": bool(delete),
    }


def default_permissions_for_role(role_key: str) -> dict[str, dict[str, bool]]:
    perms = _empty_permissions()
    if role_key == "requester":
        for module in ["dashboard", "tickets", "new_ticket", "profile", "notifications"]:
            _set(perms, module, view=True)
        _set(perms, "new_ticket", view=True, create=True)
        _set(perms, "tickets", view=True, create=True)
        return perms

    if role_key == "analyst":
        for module in ["dashboard", "tickets", "kanban", "new_ticket", "sos", "profile", "reports", "admin_use_cases", "admin_sla", "admin_corporate_areas", "admin_audit", "notifications"]:
            _set(perms, module, view=True)
        _set(perms, "tickets", view=True, create=True, edit=True)
        _set(perms, "new_ticket", view=True, create=True)
        _set(perms, "sos", view=True, create=True)
        _set(perms, "admin_use_cases", view=True, create=True, edit=True)
        return perms

    if role_key == "supervisor":
        for module in ["dashboard", "tickets", "kanban", "sos", "profile", "reports", "admin_use_cases", "admin_questions", "admin_sla", "admin_corporate_areas", "admin_audit", "notifications"]:
            _set(perms, module, view=True)
        _set(perms, "tickets", view=True, edit=True)
        return perms

    if role_key == "admin":
        for module in MODULE_KEYS:
            _set(perms, module, view=True, create=True, edit=True, delete=True)
        return perms

    return perms


def flatten_permissions(role: Role | None) -> dict[str, dict[str, bool]]:
    if not role:
        return _empty_permissions()
    perms = default_permissions_for_role(role.key)
    for permission in role.permissions:
        perms[permission.module_key] = {
            "view": bool(permission.can_view or permission.can_create or permission.can_edit or permission.can_delete),
            "create": bool(permission.can_create),
            "edit": bool(permission.can_edit),
            "delete": bool(permission.can_delete),
        }
    return perms


def get_role_by_key(db: Session, role_key: str) -> Role | None:
    return db.execute(
        select(Role).options(selectinload(Role.permissions)).where(Role.key == role_key)
    ).scalar_one_or_none()


def get_user_permissions(db: Session, user: User) -> dict[str, dict[str, bool]]:
    role = get_role_by_key(db, user.role)
    if role and role.is_active:
        return flatten_permissions(role)
    return default_permissions_for_role(user.role)


def has_permission(db: Session, user: User, module_key: str, action: str = "view") -> bool:
    if user.role == "admin":
        return True
    permissions = get_user_permissions(db, user)
    module = permissions.get(module_key)
    if not module:
        return False
    if action == "view":
        return bool(module.get("view"))
    return bool(module.get(action))


def apply_permissions(role: Role, permissions: list[dict | RolePermission]) -> None:
    role.permissions.clear()
    for item in permissions:
        data = item if isinstance(item, dict) else {
            "module_key": item.module_key,
            "can_view": item.can_view,
            "can_create": item.can_create,
            "can_edit": item.can_edit,
            "can_delete": item.can_delete,
        }
        if data["module_key"] not in MODULE_KEYS:
            continue
        role.permissions.append(RolePermission(
            module_key=data["module_key"],
            can_view=bool(data.get("can_view")),
            can_create=bool(data.get("can_create")),
            can_edit=bool(data.get("can_edit")),
            can_delete=bool(data.get("can_delete")),
        ))


def seed_roles(db: Session) -> None:
    system_roles = {
        "requester": ("Solicitante", "Usuario que crea solicitudes y ve solo sus tickets."),
        "analyst": ("Analista", "Usuario operativo que gestiona tickets de su área."),
        "supervisor": ("Supervisor", "Usuario con vista gerencial y seguimiento operativo."),
        "admin": ("Administrador", "Usuario con administración completa de la plataforma."),
    }
    for key, (name, description) in system_roles.items():
        role = get_role_by_key(db, key)
        if not role:
            role = Role(key=key, name=name, description=description, is_system=True, is_active=True)
            db.add(role)
            db.flush()
        role.name = name
        role.description = description
        role.is_system = True
        role.is_active = True
        default_permissions = default_permissions_for_role(key)
        if not role.permissions:
            permissions = []
            for module_key, values in default_permissions.items():
                permissions.append({
                    "module_key": module_key,
                    "can_view": values["view"],
                    "can_create": values["create"],
                    "can_edit": values["edit"],
                    "can_delete": values["delete"],
                })
            apply_permissions(role, permissions)
        else:
            existing_modules = {permission.module_key for permission in role.permissions}
            for module_key, values in default_permissions.items():
                if module_key not in existing_modules:
                    role.permissions.append(RolePermission(
                        module_key=module_key,
                        can_view=values["view"],
                        can_create=values["create"],
                        can_edit=values["edit"],
                        can_delete=values["delete"],
                    ))
