from datetime import datetime
from app.core.timezone import now_utc_naive, frontend_local_to_utc_naive
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload
from app.api.deps import get_current_user, require_permission
from app.core.database import get_db
from app.core.security import get_password_hash, validate_password_policy
from app.models.user import User
from app.models.ticket import Ticket, TicketComment, TicketAttachment
from app.models.sos import SOSEvent
from app.models.category import Category
from app.models.sla import SLAPolicy
from app.models.audit import AuditLog
from app.models.corporate_area import CorporateArea
from app.models.required_question import RequiredQuestion
from app.models.role import Role
from app.schemas.user import UserCreate, UserUpdate, UserOut, UserPasswordReset
from app.schemas.category import CategoryCreate, CategoryUpdate, CategoryOut
from app.schemas.sla import SLAPolicyCreate, SLAPolicyUpdate, SLAPolicyOut
from app.schemas.corporate_area import CorporateAreaCreate, CorporateAreaUpdate, CorporateAreaOut
from app.schemas.required_question import RequiredQuestionCreate, RequiredQuestionUpdate, RequiredQuestionOut
from app.schemas.role import RoleCreate, RoleUpdate, RoleOut, RoleModuleOut
from app.services.required_question_service import make_question_key
from app.services.audit_service import write_audit
from app.services.role_service import ROLE_MODULES, apply_permissions
from app.services.output_service import user_public_dict
from app.services.authorization_service import resolve_user_ref, deny_with_audit

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/role-modules", response_model=list[RoleModuleOut])
def role_modules(current_user: User = Depends(require_permission("admin_roles", "view"))):
    return ROLE_MODULES


@router.get("/roles", response_model=list[RoleOut])
def list_roles(db: Session = Depends(get_db), current_user: User = Depends(require_permission("admin_roles", "view"))):
    return list(db.execute(select(Role).options(selectinload(Role.permissions)).order_by(Role.is_system.desc(), Role.name)).scalars().unique().all())


@router.post("/roles", response_model=RoleOut)
def create_role(payload: RoleCreate, db: Session = Depends(get_db), current_user: User = Depends(require_permission("admin_roles", "create"))):
    key = payload.key.strip().lower()
    exists = db.execute(select(Role).where(Role.key == key)).scalar_one_or_none()
    if exists:
        raise HTTPException(status_code=400, detail="El rol ya existe")
    role = Role(key=key, name=payload.name, description=payload.description, is_system=False, is_active=payload.is_active)
    db.add(role)
    db.flush()
    apply_permissions(role, [item.model_dump() for item in payload.permissions])
    write_audit(db, actor=current_user, entity_type="role", entity_id=role.id, action="create", new_value=role.key)
    db.commit()
    return db.execute(select(Role).options(selectinload(Role.permissions)).where(Role.id == role.id)).scalar_one()


@router.patch("/roles/{role_id}", response_model=RoleOut)
def update_role(role_id: int, payload: RoleUpdate, db: Session = Depends(get_db), current_user: User = Depends(require_permission("admin_roles", "edit"))):
    role = db.execute(select(Role).options(selectinload(Role.permissions)).where(Role.id == role_id)).scalar_one_or_none()
    if not role:
        raise HTTPException(status_code=404, detail="Rol no encontrado")
    old = f"{role.key}|{role.name}|{role.is_active}|{[(p.module_key, p.can_view, p.can_create, p.can_edit, p.can_delete) for p in role.permissions]}"
    data = payload.model_dump(exclude_unset=True)
    if "name" in data and data["name"] is not None:
        role.name = data["name"]
    if "description" in data:
        role.description = data["description"]
    if "is_active" in data and data["is_active"] is not None:
        if role.is_system and data["is_active"] is False:
            raise HTTPException(status_code=400, detail="No se puede desactivar un rol de sistema")
        role.is_active = data["is_active"]
    if payload.permissions is not None:
        apply_permissions(role, [item.model_dump() for item in payload.permissions])
    write_audit(db, actor=current_user, entity_type="role", entity_id=role.id, action="update", old_value=old, new_value=str(data))
    db.commit()
    return db.execute(select(Role).options(selectinload(Role.permissions)).where(Role.id == role.id)).scalar_one()


@router.get("/corporate-areas", response_model=list[CorporateAreaOut])
def corporate_areas(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    include_inactive: bool = Query(default=False),
):
    # El formulario de tickets consume esta ruta. Los inactivos quedan restringidos a administración.
    if current_user.role == "requester":
        include_inactive = False
    query = select(CorporateArea)
    if not include_inactive:
        query = query.where(CorporateArea.is_active.is_(True))
    query = query.order_by(CorporateArea.name)
    return list(db.execute(query).scalars().all())


@router.post("/corporate-areas", response_model=CorporateAreaOut)
def create_corporate_area(payload: CorporateAreaCreate, db: Session = Depends(get_db), current_user: User = Depends(require_permission("admin_corporate_areas", "create"))):
    name = payload.name.strip().upper()
    exists = db.execute(select(CorporateArea).where(CorporateArea.name == name)).scalar_one_or_none()
    if exists:
        if not exists.is_active:
            exists.is_active = True
            exists.description = payload.description
            write_audit(db, actor=current_user, entity_type="corporate_area", entity_id=exists.id, action="reactivate", new_value=exists.name)
            db.commit()
            db.refresh(exists)
        return exists
    area = CorporateArea(name=name, description=payload.description, is_active=payload.is_active)
    db.add(area)
    db.flush()
    write_audit(db, actor=current_user, entity_type="corporate_area", entity_id=area.id, action="create", new_value=area.name)
    db.commit()
    db.refresh(area)
    return area


@router.patch("/corporate-areas/{area_id}", response_model=CorporateAreaOut)
def update_corporate_area(area_id: int, payload: CorporateAreaUpdate, db: Session = Depends(get_db), current_user: User = Depends(require_permission("admin_corporate_areas", "edit"))):
    area = db.get(CorporateArea, area_id)
    if not area:
        raise HTTPException(status_code=404, detail="Área corporativa no encontrada")
    old = f"{area.name}|{area.description}|{area.is_active}"
    data = payload.model_dump(exclude_unset=True)
    if "name" in data and data["name"]:
        data["name"] = data["name"].strip().upper()
    for key, value in data.items():
        setattr(area, key, value)
    write_audit(db, actor=current_user, entity_type="corporate_area", entity_id=area.id, action="update", old_value=old, new_value=str(data))
    db.commit()
    db.refresh(area)
    return area


@router.get("/users", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db), current_user: User = Depends(require_permission("admin_users", "view"))):
    users = list(db.execute(select(User).where(User.is_deleted.is_(False)).order_by(User.full_name)).scalars().all())
    return [user_public_dict(user) for user in users]


@router.post("/users", response_model=UserOut)
def create_user(payload: UserCreate, db: Session = Depends(get_db), current_user: User = Depends(require_permission("admin_users", "create"))):
    exists = db.execute(select(User).where(User.email == payload.email)).scalar_one_or_none()
    if exists:
        raise HTTPException(status_code=400, detail="El correo ya existe")
    role = db.execute(select(Role).where(Role.key == payload.role, Role.is_active.is_(True))).scalar_one_or_none()
    if not role:
        raise HTTPException(status_code=400, detail="Rol inválido o inactivo")
    try:
        validate_password_policy(payload.password, str(payload.email))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    user = User(
        email=payload.email,
        full_name=payload.full_name,
        hashed_password=get_password_hash(payload.password),
        role=payload.role,
        area=payload.area,
    )
    db.add(user)
    db.flush()
    write_audit(db, actor=current_user, entity_type="user", entity_id=user.public_id, action="create", new_value=user.email)
    db.commit()
    db.refresh(user)
    return user_public_dict(user)


@router.patch("/users/{user_id}", response_model=UserOut)
def update_user(user_id: str, payload: UserUpdate, db: Session = Depends(get_db), current_user: User = Depends(require_permission("admin_users", "edit"))):
    user = resolve_user_ref(db, user_id)
    if not user or user.is_deleted:
        deny_with_audit(db, actor=current_user, entity_type="user", entity_id=str(user_id), action="user_access_denied", detail="Usuario no encontrado")
    old = f"{user.full_name}|{user.role}|{user.area}|{user.is_active}"
    data = payload.model_dump(exclude_unset=True)
    new_password = data.pop("new_password", None)
    if "role" in data and data["role"]:
        role = db.execute(select(Role).where(Role.key == data["role"], Role.is_active.is_(True))).scalar_one_or_none()
        if not role:
            raise HTTPException(status_code=400, detail="Rol inválido o inactivo")
    if current_user.id == user.id and data.get("is_active") is False:
        raise HTTPException(status_code=400, detail="No puedes desactivar tu propia cuenta")
    for key, value in data.items():
        setattr(user, key, value)
    if new_password:
        try:
            validate_password_policy(new_password, user.email)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
        user.hashed_password = get_password_hash(new_password)
        write_audit(db, actor=current_user, entity_type="user", entity_id=user.public_id, action="reset_password", new_value=user.email)
    write_audit(db, actor=current_user, entity_type="user", entity_id=user.public_id, action="update", old_value=old, new_value=str({k: v for k, v in data.items()}))
    db.commit()
    db.refresh(user)
    return user_public_dict(user)


@router.post("/users/{user_id}/reset-password")
def reset_user_password(user_id: str, payload: UserPasswordReset, db: Session = Depends(get_db), current_user: User = Depends(require_permission("admin_users", "edit"))):
    user = resolve_user_ref(db, user_id)
    if not user or user.is_deleted:
        deny_with_audit(db, actor=current_user, entity_type="user", entity_id=str(user_id), action="user_access_denied", detail="Usuario no encontrado")
    try:
        validate_password_policy(payload.new_password, user.email)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    user.hashed_password = get_password_hash(payload.new_password)
    write_audit(db, actor=current_user, entity_type="user", entity_id=user.public_id, action="reset_password", new_value=user.email)
    db.commit()
    return {"ok": True, "message": "Contraseña actualizada correctamente"}


@router.delete("/users/{user_id}")
def delete_user(user_id: str, db: Session = Depends(get_db), current_user: User = Depends(require_permission("admin_users", "delete"))):
    user = resolve_user_ref(db, user_id)
    if not user or user.is_deleted:
        deny_with_audit(db, actor=current_user, entity_type="user", entity_id=str(user_id), action="user_access_denied", detail="Usuario no encontrado")
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="No puedes eliminar tu propia cuenta")

    active_admins = list(db.execute(
        select(User).where(User.role == "admin", User.is_active.is_(True), User.is_deleted.is_(False))
    ).scalars().all())
    if user.role == "admin" and len(active_admins) <= 1:
        raise HTTPException(status_code=400, detail="No puedes eliminar el último administrador activo")

    old = f"{user.email}|{user.full_name}|{user.role}|{user.area}|{user.is_active}"
    user.is_active = False
    user.is_deleted = True
    user.deleted_at = now_utc_naive()
    write_audit(db, actor=current_user, entity_type="user", entity_id=user.public_id, action="delete", old_value=old, new_value="soft_delete")
    db.commit()
    return {"ok": True, "message": "Usuario eliminado correctamente"}


@router.get("/categories", response_model=list[CategoryOut])
def list_categories(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("admin_use_cases", "view")),
    area: str | None = Query(default=None),
    severity: str | None = Query(default=None),
    include_inactive: bool = Query(default=False),
):
    query = select(Category)
    if not include_inactive:
        query = query.where(Category.is_active.is_(True))
    if area:
        query = query.where(Category.area == area)
    if severity:
        query = query.where(Category.severity == severity)
    query = query.order_by(Category.area, Category.severity, Category.name)
    return list(db.execute(query).scalars().all())


@router.post("/categories", response_model=CategoryOut)
def create_category(payload: CategoryCreate, db: Session = Depends(get_db), current_user: User = Depends(require_permission("admin_use_cases", "create"))):
    exists = db.execute(
        select(Category).where(Category.area == payload.area, Category.severity == payload.severity, Category.name == payload.name)
    ).scalar_one_or_none()
    if exists:
        if not exists.is_active:
            exists.is_active = True
            write_audit(db, actor=current_user, entity_type="category", entity_id=exists.id, action="reactivate", new_value=exists.name)
            db.commit()
            db.refresh(exists)
        return exists
    category = Category(**payload.model_dump())
    db.add(category)
    db.flush()
    write_audit(db, actor=current_user, entity_type="category", entity_id=category.id, action="create", new_value=f"{category.area}|{category.severity}|{category.name}")
    db.commit()
    db.refresh(category)
    return category


@router.patch("/categories/{category_id}", response_model=CategoryOut)
def update_category(category_id: int, payload: CategoryUpdate, db: Session = Depends(get_db), current_user: User = Depends(require_permission("admin_use_cases", "edit"))):
    category = db.get(Category, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Caso de uso no encontrado")
    old = f"{category.area}|{category.severity}|{category.name}|{category.is_active}|{category.description}"
    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(category, key, value)
    write_audit(db, actor=current_user, entity_type="category", entity_id=category.id, action="update", old_value=old, new_value=str(data))
    db.commit()
    db.refresh(category)
    return category


@router.get("/sla", response_model=list[SLAPolicyOut])
def list_sla(db: Session = Depends(get_db), current_user: User = Depends(require_permission("admin_sla", "view"))):
    return list(db.execute(select(SLAPolicy).order_by(SLAPolicy.severity)).scalars().all())


@router.post("/sla", response_model=SLAPolicyOut)
def create_sla(payload: SLAPolicyCreate, db: Session = Depends(get_db), current_user: User = Depends(require_permission("admin_sla", "create"))):
    policy = SLAPolicy(**payload.model_dump())
    db.add(policy)
    db.flush()
    write_audit(db, actor=current_user, entity_type="sla_policy", entity_id=policy.id, action="create", new_value=f"{policy.area}|{policy.severity}")
    db.commit()
    db.refresh(policy)
    return policy


@router.patch("/sla/{sla_id}", response_model=SLAPolicyOut)
def update_sla(sla_id: int, payload: SLAPolicyUpdate, db: Session = Depends(get_db), current_user: User = Depends(require_permission("admin_sla", "edit"))):
    policy = db.get(SLAPolicy, sla_id)
    if not policy:
        raise HTTPException(status_code=404, detail="Política SLA no encontrada")
    old = f"{policy.area}|{policy.severity}|{policy.first_response_minutes}|{policy.resolution_minutes}|{policy.business_hours_only}|{policy.pause_allowed}|{policy.active}"
    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(policy, key, value)
    write_audit(db, actor=current_user, entity_type="sla_policy", entity_id=policy.id, action="update", old_value=old, new_value=str(data))
    db.commit()
    db.refresh(policy)
    return policy


@router.get("/audit")
def audit_log(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("admin_audit", "view")),
    actor_user_id: int | None = Query(default=None),
    action: str | None = Query(default=None),
    entity_type: str | None = Query(default=None),
    entity_id: str | None = Query(default=None),
    date_from: datetime | None = Query(default=None),
    date_to: datetime | None = Query(default=None),
    limit: int = Query(default=500, ge=1, le=1000),
):
    query = select(AuditLog)
    if actor_user_id is not None:
        query = query.where(AuditLog.actor_user_id == actor_user_id)
    if action:
        query = query.where(AuditLog.action.ilike(f"%{action}%"))
    if entity_type:
        query = query.where(AuditLog.entity_type == entity_type)
    if entity_id is not None:
        query = query.where(AuditLog.entity_id == str(entity_id))
    if date_from:
        query = query.where(AuditLog.timestamp >= (frontend_local_to_utc_naive(date_from) or date_from))
    if date_to:
        query = query.where(AuditLog.timestamp <= (frontend_local_to_utc_naive(date_to) or date_to))
    logs = db.execute(query.order_by(AuditLog.id.desc()).limit(limit)).scalars().all()
    return [
        {
            "id": log.id,
            "timestamp": log.timestamp,
            "actor_user_id": log.actor_user_id,
            "actor_role": log.actor_role,
            "entity_type": log.entity_type,
            "entity_id": log.entity_id,
            "action": log.action,
            "old_value": log.old_value,
            "new_value": log.new_value,
            "source_ip": log.source_ip,
            "user_agent": log.user_agent,
            "previous_hash": log.previous_hash,
            "current_hash": log.current_hash,
        }
        for log in logs
    ]


@router.get("/required-questions", response_model=list[RequiredQuestionOut])
def list_required_questions(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("admin_questions", "view")),
    area: str | None = Query(default=None),
    severity: str | None = Query(default=None),
    category: str | None = Query(default=None),
    include_inactive: bool = Query(default=True),
):
    query = select(RequiredQuestion)
    if area:
        query = query.where(RequiredQuestion.area == area)
    if severity:
        query = query.where(RequiredQuestion.severity == severity)
    if category:
        query = query.where(RequiredQuestion.category == category)
    if not include_inactive:
        query = query.where(RequiredQuestion.is_active.is_(True))
    query = query.order_by(RequiredQuestion.area, RequiredQuestion.severity, RequiredQuestion.category, RequiredQuestion.sort_order, RequiredQuestion.id)
    return list(db.execute(query).scalars().all())


@router.post("/required-questions", response_model=RequiredQuestionOut)
def create_required_question(payload: RequiredQuestionCreate, db: Session = Depends(get_db), current_user: User = Depends(require_permission("admin_questions", "create"))):
    key = payload.question_key or make_question_key(payload.question_text, prefix=f"{payload.area[:3]}_{payload.severity[:3]}")
    question = RequiredQuestion(**payload.model_dump(exclude={"question_key"}), question_key=key)
    db.add(question)
    db.flush()
    write_audit(db, actor=current_user, entity_type="required_question", entity_id=question.id, action="create", new_value=f"{question.area}|{question.severity}|{question.category}|{question.question_text}")
    db.commit()
    db.refresh(question)
    return question


@router.patch("/required-questions/{question_id}", response_model=RequiredQuestionOut)
def update_required_question(question_id: int, payload: RequiredQuestionUpdate, db: Session = Depends(get_db), current_user: User = Depends(require_permission("admin_questions", "edit"))):
    question = db.get(RequiredQuestion, question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Pregunta requerida no encontrada")
    old = f"{question.area}|{question.severity}|{question.category}|{question.question_text}|{question.required}|{question.is_active}"
    data = payload.model_dump(exclude_unset=True)
    if not data.get("question_key") and data.get("question_text"):
        data["question_key"] = make_question_key(data["question_text"], prefix=f"{question.area[:3]}_{question.severity[:3]}")
    for key, value in data.items():
        setattr(question, key, value)
    write_audit(db, actor=current_user, entity_type="required_question", entity_id=question.id, action="update", old_value=old, new_value=str(data))
    db.commit()
    db.refresh(question)
    return question


@router.delete("/required-questions/{question_id}")
def delete_required_question(question_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_permission("admin_questions", "delete"))):
    question = db.get(RequiredQuestion, question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Pregunta requerida no encontrada")
    old = f"{question.area}|{question.severity}|{question.category}|{question.question_text}"
    db.delete(question)
    write_audit(db, actor=current_user, entity_type="required_question", entity_id=question_id, action="delete", old_value=old)
    db.commit()
    return {"ok": True}
