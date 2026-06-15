import csv
import hashlib
import io
import re
import shutil
from datetime import datetime
from app.core.timezone import now_utc_naive, frontend_local_to_utc_naive
from pathlib import Path
from uuid import uuid4
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Response, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import select, or_
from sqlalchemy.orm import Session, selectinload
from app.api.deps import get_current_user, get_analysts_by_area, require_roles
from app.core.database import get_db
from app.core.config import settings
from app.models.category import Category
from app.models.ticket import Ticket, TicketAttachment, TicketComment, TicketDynamicAnswer
from app.models.user import User
from app.schemas.ticket import (
    TicketCreate,
    TicketOut,
    TicketStatusUpdate,
    TicketAssign,
    TicketCommentCreate,
    ChecklistResponse,
)
from app.services.audit_service import write_audit
from app.services.required_question_service import get_required_questions
from app.services.ticket_catalog_service import get_severity_catalog
from app.services.notification_service import (
    notify_ticket_created,
    notify_ticket_assigned,
    notify_ticket_commented,
    notify_ticket_resolved,
    notify_ticket_closed,
    notify_ticket_status_changed,
)
from app.services.sla_service import apply_initial_sla, pause_sla, resume_sla, refresh_breach, get_sla_snapshot, find_sla_policy
from app.services.role_service import has_permission
from app.services.authorization_service import (
    has_global_ticket_scope as _auth_has_global_ticket_scope,
    require_view_ticket,
    require_manage_ticket,
    resolve_user_ref,
    can_view_ticket,
    deny_with_audit,
)

router = APIRouter(prefix="/tickets", tags=["tickets"])
UPLOAD_DIR = settings.upload_path
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
ALLOWED_EXTENSIONS = settings.allowed_upload_extensions
BLOCKED_EXTENSIONS = settings.blocked_upload_extensions


def _safe_filename(filename: str) -> str:
    name = Path(filename or "archivo").name
    name = re.sub(r"[^A-Za-z0-9._ -]", "_", name).strip(". ")
    return name[:180] or "archivo"


def _detect_mime_from_bytes(sample: bytes, original_name: str) -> str:
    """Detección liviana de tipo real para evitar confiar solo en content-type del navegador."""
    lower_name = original_name.lower()
    if sample.startswith(b"%PDF-"):
        return "application/pdf"
    if sample.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if sample.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if sample.startswith(b"GIF87a") or sample.startswith(b"GIF89a"):
        return "image/gif"
    if sample.startswith(b"RIFF") and b"WEBP" in sample[:16]:
        return "image/webp"
    if sample.startswith(b"PK\x03\x04") or sample.startswith(b"PK\x05\x06") or sample.startswith(b"PK\x07\x08"):
        if lower_name.endswith(".docx"):
            return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        if lower_name.endswith(".xlsx"):
            return "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        return "application/zip"
    if sample[:512].lstrip().lower().startswith((b"<html", b"<!doctype html", b"<script", b"<?php", b"<svg")):
        return "application/x-blocked-active-content"
    return "application/octet-stream"


def _save_upload(file: UploadFile) -> tuple[str, str, int, str, str]:
    original_name = _safe_filename(file.filename or "archivo")
    extension = Path(original_name).suffix.lower()
    if extension in BLOCKED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Extensión bloqueada por seguridad: {extension}")
    if extension and extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Extensión no permitida: {extension}")
    stored_name = f"{uuid4().hex}{extension}"
    destination = UPLOAD_DIR / stored_name
    size = 0
    digest = hashlib.sha256()
    sample = b""
    with destination.open("wb") as buffer:
        while True:
            chunk = file.file.read(1024 * 1024)
            if not chunk:
                break
            if not sample:
                sample = chunk[:2048]
            size += len(chunk)
            if size > settings.max_upload_size_bytes:
                buffer.close()
                destination.unlink(missing_ok=True)
                raise HTTPException(status_code=413, detail=f"El archivo supera el máximo permitido de {settings.MAX_UPLOAD_SIZE_MB} MB")
            digest.update(chunk)
            buffer.write(chunk)
    detected_mime = _detect_mime_from_bytes(sample, original_name)
    if detected_mime == "application/x-blocked-active-content":
        destination.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail="Contenido activo no permitido en evidencias")
    return original_name, stored_name, size, digest.hexdigest(), detected_mime


def _ensure_can_view_tickets(db: Session, user: User) -> None:
    if has_permission(db, user, "tickets", "view"):
        return
    raise HTTPException(status_code=403, detail="Permiso insuficiente para ver tickets")


def _ensure_can_create_ticket(db: Session, user: User) -> None:
    if has_permission(db, user, "new_ticket", "create") or has_permission(db, user, "tickets", "create"):
        return
    raise HTTPException(status_code=403, detail="Permiso insuficiente para crear tickets")


def _ensure_can_manage_ticket(db: Session, user: User) -> None:
    if has_permission(db, user, "tickets", "edit"):
        return
    raise HTTPException(status_code=403, detail="Permiso insuficiente para gestionar tickets")


def _has_global_ticket_scope(db: Session, user: User) -> bool:
    return _auth_has_global_ticket_scope(db, user)

def _next_ticket_number(db: Session) -> str:
    year = now_utc_naive().year
    count = db.execute(select(Ticket)).scalars().all()
    return f"TCK-{year}-{len(count) + 1:05d}"


def _query_visible_tickets(db: Session, user: User):
    query = select(Ticket).options(
        selectinload(Ticket.created_by),
        selectinload(Ticket.assigned_to),
        selectinload(Ticket.dynamic_answers),
        selectinload(Ticket.comments).selectinload(TicketComment.author),
        selectinload(Ticket.comments).selectinload(TicketComment.attachments).selectinload(TicketAttachment.uploaded_by),
        selectinload(Ticket.attachments).selectinload(TicketAttachment.uploaded_by),
    )
    if _has_global_ticket_scope(db, user):
        return query
    if user.role == "analyst" and user.area:
        return query.where(or_(Ticket.area_destino == user.area, Ticket.assigned_to_id == user.id, Ticket.created_by_id == user.id))
    return query.where(Ticket.created_by_id == user.id)


def _get_visible_ticket(db: Session, ticket_id: str | int, user: User) -> Ticket:
    return require_view_ticket(db, user, ticket_id)


def _attachment_to_out(attachment: TicketAttachment) -> dict:
    return {
        "id": attachment.public_id,
        "file_name": attachment.file_name,
        "content_type": attachment.content_type,
        "detected_mime": getattr(attachment, "detected_mime", None),
        "sha256_hash": getattr(attachment, "sha256_hash", None),
        "security_scan_status": getattr(attachment, "security_scan_status", "validated"),
        "size_bytes": attachment.size_bytes,
        "created_at": attachment.created_at,
        "uploaded_by_id": attachment.uploaded_by.public_id if attachment.uploaded_by else "",
        "uploaded_by_name": attachment.uploaded_by.full_name if attachment.uploaded_by else None,
        "comment_id": attachment.comment.public_id if attachment.comment else None,
        "download_url": f"/api/v1/tickets/{attachment.ticket.public_id}/attachments/{attachment.public_id}/download",
    }


def _ticket_to_out(ticket: Ticket, user: User, db: Session) -> dict:
    """Serializa el ticket filtrando notas internas y sus adjuntos para solicitantes."""
    comments = ticket.comments
    if user.role == "requester":
        comments = [c for c in comments if c.comment_type != "internal"]

    sla_snapshot = get_sla_snapshot(db, ticket)
    return {
        "id": ticket.public_id,
        "ticket_number": ticket.ticket_number,
        "created_by_id": ticket.created_by.public_id if ticket.created_by else "",
        "created_by_name": ticket.created_by.full_name if ticket.created_by else None,
        "created_by_email": ticket.created_by.email if ticket.created_by else None,
        "assigned_to_id": ticket.assigned_to.public_id if ticket.assigned_to else None,
        "assigned_to_name": ticket.assigned_to.full_name if ticket.assigned_to else None,
        "assigned_to_email": ticket.assigned_to.email if ticket.assigned_to else None,
        "area_destino": ticket.area_destino,
        "project_area": ticket.project_area,
        "category": ticket.category,
        "severity": ticket.severity,
        "status": ticket.status,
        "subject": ticket.subject,
        "description": ticket.description,
        "involved_asset": ticket.involved_asset,
        "first_event_at": ticket.first_event_at,
        "evidence_summary": ticket.evidence_summary,
        "ip_address": ticket.ip_address,
        "hostname": ticket.hostname,
        "impact": ticket.impact,
        "scope_users_affected": ticket.scope_users_affected,
        "deadline": ticket.deadline,
        "deadline_justification": ticket.deadline_justification,
        "created_at": ticket.created_at,
        "updated_at": ticket.updated_at,
        "assigned_at": ticket.assigned_at,
        "first_response_at": ticket.first_response_at,
        "resolved_at": ticket.resolved_at,
        "closed_at": ticket.closed_at,
        "sla_due_at": ticket.sla_due_at,
        "sla_paused_seconds": ticket.sla_paused_seconds,
        "is_sla_breached": ticket.is_sla_breached,
        **sla_snapshot,
        "dynamic_answers": [
            {"id": a.id, "question_key": a.question_key, "question_text": a.question_text, "answer": a.answer, "required": a.required}
            for a in sorted(ticket.dynamic_answers, key=lambda item: item.id)
        ],
        "comments": [
            {
                "id": c.public_id,
                "author_id": c.author.public_id if c.author else "",
                "author_name": c.author.full_name if c.author else None,
                "comment_type": c.comment_type,
                "body": c.body,
                "created_at": c.created_at,
                "attachments": [_attachment_to_out(a) for a in sorted(c.attachments, key=lambda item: item.created_at)],
            }
            for c in sorted(comments, key=lambda item: item.created_at)
        ],
        "attachments": [
            _attachment_to_out(a)
            for a in sorted([item for item in ticket.attachments if item.comment_id is None], key=lambda item: item.created_at, reverse=True)
        ],
    }


def _use_cases_from_db(db: Session, area: str, severity: str) -> list[str]:
    rows = db.execute(
        select(Category)
        .where(Category.area == area, Category.severity == severity, Category.is_active.is_(True))
        .order_by(Category.name)
    ).scalars().all()
    return [row.name for row in rows]


def _ensure_category_from_ticket(db: Session, ticket: Ticket, actor: User) -> None:
    exists = db.execute(
        select(Category).where(Category.area == ticket.area_destino, Category.severity == ticket.severity, Category.name == ticket.category)
    ).scalar_one_or_none()
    if exists:
        if not exists.is_active:
            exists.is_active = True
            write_audit(db, actor=actor, entity_type="category", entity_id=exists.id, action="reactivate_from_ticket", new_value=exists.name)
        return
    category = Category(
        area=ticket.area_destino,
        severity=ticket.severity,
        name=ticket.category,
        description=f"Añadido desde creación de ticket {ticket.ticket_number} por {actor.email}",
        is_active=True,
    )
    db.add(category)
    db.flush()
    write_audit(db, actor=actor, entity_type="category", entity_id=category.id, action="create_from_ticket", new_value=f"{category.area}|{category.severity}|{category.name}")


@router.get("/catalog")
def ticket_catalog(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _ensure_can_view_tickets(db, current_user)
    categories = db.execute(select(Category).where(Category.is_active.is_(True)).order_by(Category.area, Category.severity, Category.name)).scalars().all()
    grouped: dict[str, dict[str, list[str]]] = {}
    for category in categories:
        grouped.setdefault(category.area, {}).setdefault(category.severity, []).append(category.name)
    return grouped


@router.get("/checklist", response_model=ChecklistResponse)
def checklist(
    area: str = Query(...),
    severity: str = Query(...),
    category: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not (has_permission(db, current_user, "new_ticket", "view") or has_permission(db, current_user, "tickets", "view")):
        raise HTTPException(status_code=403, detail="Permiso insuficiente para consultar matriz de tickets")
    catalog = get_severity_catalog(area, severity)
    use_cases = _use_cases_from_db(db, area, severity)
    if not use_cases and catalog:
        use_cases = catalog.use_cases
    return ChecklistResponse(
        area=area,
        severity=severity,
        category=category,
        channel=catalog.channel if catalog else None,
        sla_mode=catalog.sla_mode if catalog else None,
        description=catalog.description if catalog else None,
        use_cases=use_cases,
        questions=get_required_questions(db, area, severity, category),
    )


@router.post("", response_model=TicketOut)
def create_ticket(payload: TicketCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _ensure_can_create_ticket(db, current_user)
    if "crítica" in payload.severity.lower() or "sos" in payload.severity.lower():
        raise HTTPException(status_code=400, detail="La severidad Crítica/SOS no se inicia por ticket. Debe registrarse como evento SOS posterior a la llamada.")

    if not payload.category.strip():
        raise HTTPException(status_code=400, detail="Debe seleccionar o ingresar un caso de uso")
    if not payload.project_area.strip():
        raise HTTPException(status_code=400, detail="Debe seleccionar el área corporativa solicitante")
    if not payload.description.strip():
        raise HTTPException(status_code=400, detail="Debe ingresar una descripción breve de la solicitud")

    expected_questions = get_required_questions(db, payload.area_destino, payload.severity, payload.category.strip())
    answers_by_key = {item.question_key: (item.answer or "").strip() for item in payload.dynamic_answers}
    missing_questions = [q.text for q in expected_questions if q.required and not answers_by_key.get(q.key)]
    if missing_questions:
        raise HTTPException(status_code=400, detail="Faltan preguntas requeridas: " + "; ".join(missing_questions[:5]))

    ticket = Ticket(
        ticket_number=_next_ticket_number(db),
        created_by_id=current_user.id,
        area_destino=payload.area_destino,
        project_area=payload.project_area,
        category=payload.category.strip(),
        severity=payload.severity,
        subject=payload.subject,
        description=payload.description,
        involved_asset=payload.involved_asset,
        first_event_at=frontend_local_to_utc_naive(payload.first_event_at) or now_utc_naive(),
        evidence_summary=payload.evidence_summary,
        ip_address=payload.ip_address,
        hostname=payload.hostname,
        impact=payload.impact,
        scope_users_affected=payload.scope_users_affected,
        deadline=frontend_local_to_utc_naive(payload.deadline),
        deadline_justification=payload.deadline_justification,
    )
    db.add(ticket)
    db.flush()
    _ensure_category_from_ticket(db, ticket, current_user)
    for answer in payload.dynamic_answers:
        db.add(TicketDynamicAnswer(ticket_id=ticket.id, **answer.model_dump()))
    apply_initial_sla(db, ticket)
    write_audit(db, actor=current_user, entity_type="ticket", entity_id=ticket.public_id, action="create", new_value=ticket.ticket_number)
    notify_ticket_created(db, ticket, get_analysts_by_area(db, ticket.area_destino))
    db.commit()
    db.refresh(ticket)
    return _ticket_to_out(_get_visible_ticket(db, ticket.id, current_user), current_user, db)


@router.get("", response_model=list[TicketOut])
def list_tickets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    status: str | None = None,
    severity: str | None = None,
    area: str | None = None,
):
    _ensure_can_view_tickets(db, current_user)
    query = _query_visible_tickets(db, current_user).order_by(Ticket.updated_at.desc())
    if status:
        query = query.where(Ticket.status == status)
    if severity:
        query = query.where(Ticket.severity == severity)
    if area:
        query = query.where(Ticket.area_destino == area)
    tickets = list(db.execute(query).scalars().unique().all())
    for ticket in tickets:
        refresh_breach(ticket)
    db.commit()
    return [_ticket_to_out(ticket, current_user, db) for ticket in tickets]


@router.get("/export.csv")
def export_csv(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not (has_permission(db, current_user, "reports", "view") or has_permission(db, current_user, "tickets", "edit")):
        raise HTTPException(status_code=403, detail="Permiso insuficiente para exportar tickets")
    tickets = list(db.execute(_query_visible_tickets(db, current_user)).scalars().unique().all())
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["public_id", "ticket_number", "category", "created_by", "assigned_to", "created_at", "updated_at", "resolved_at", "status", "severity"])
    for t in tickets:
        writer.writerow([t.public_id, t.ticket_number, t.category, t.created_by.email if t.created_by else "", t.assigned_to.email if t.assigned_to else "", t.created_at, t.updated_at, t.resolved_at, t.status, t.severity])
    return Response(content=output.getvalue(), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=tickets.csv"})


@router.get("/assignees")
def list_assignees(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _ensure_can_manage_ticket(db, current_user)
    users = db.execute(
        select(User)
        .where(User.is_active.is_(True))
        .where(User.is_deleted.is_(False))
        .where(User.role.in_(["analyst", "admin", "supervisor"]))
        .order_by(User.full_name)
    ).scalars().all()
    return [
        {"id": user.public_id, "full_name": user.full_name, "email": user.email, "role": user.role, "area": user.area}
        for user in users
    ]


@router.get("/{ticket_id}", response_model=TicketOut)
def get_ticket(ticket_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _ensure_can_view_tickets(db, current_user)
    ticket = _get_visible_ticket(db, ticket_id, current_user)
    refresh_breach(ticket)
    db.commit()
    return _ticket_to_out(ticket, current_user, db)


@router.patch("/{ticket_id}/assign", response_model=TicketOut)
def assign_ticket(ticket_id: str, payload: TicketAssign, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _ensure_can_manage_ticket(db, current_user)
    ticket = _get_visible_ticket(db, ticket_id, current_user)
    assignee = resolve_user_ref(db, payload.assigned_to_id)
    if not assignee or assignee.is_deleted or not assignee.is_active:
        raise HTTPException(status_code=404, detail="Usuario asignable no encontrado")
    if assignee.role not in ["analyst", "admin", "supervisor"]:
        raise HTTPException(status_code=400, detail="El usuario no puede ser asignado a tickets")
    old = ticket.assigned_to_id
    ticket.assigned_to_id = assignee.id
    ticket.status = "Asignado"
    if not ticket.assigned_at:
        ticket.assigned_at = now_utc_naive()
    if not ticket.first_response_at:
        ticket.first_response_at = now_utc_naive()
    write_audit(db, actor=current_user, entity_type="ticket", entity_id=ticket.public_id, action="assign", old_value=str(old), new_value=assignee.public_id)
    notify_ticket_assigned(db, ticket)
    db.commit()
    return _ticket_to_out(_get_visible_ticket(db, ticket_id, current_user), current_user, db)


@router.patch("/{ticket_id}/status", response_model=TicketOut)
def update_status(ticket_id: str, payload: TicketStatusUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _ensure_can_manage_ticket(db, current_user)
    ticket = _get_visible_ticket(db, ticket_id, current_user)
    old_status = ticket.status
    policy = find_sla_policy(db, ticket.area_destino, ticket.severity)
    if old_status == "En Espera" and payload.status != "En Espera":
        resume_sla(ticket)
    if payload.status == "En Espera" and (policy is None or policy.pause_allowed):
        pause_sla(ticket)
    if payload.status in ["Asignado", "En Progreso"] and not ticket.first_response_at:
        ticket.first_response_at = now_utc_naive()
    if payload.status == "Resuelto" and not ticket.resolved_at:
        ticket.resolved_at = now_utc_naive()
        notify_ticket_resolved(db, ticket)
    if payload.status == "Cerrado" and not ticket.closed_at:
        ticket.closed_at = now_utc_naive()
        notify_ticket_closed(db, ticket)
    ticket.status = payload.status
    refresh_breach(ticket)
    notify_ticket_status_changed(db, ticket, old_status=old_status, new_status=payload.status, actor=current_user)
    write_audit(db, actor=current_user, entity_type="ticket", entity_id=ticket.public_id, action="status_change", old_value=old_status, new_value=payload.status)
    if payload.reason:
        db.add(TicketComment(ticket_id=ticket.id, author_id=current_user.id, comment_type="system", body=f"Cambio de estado: {payload.reason}"))
    db.commit()
    return _ticket_to_out(_get_visible_ticket(db, ticket_id, current_user), current_user, db)


@router.post("/{ticket_id}/comments", response_model=TicketOut)
def add_comment(ticket_id: str, payload: TicketCommentCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _ensure_can_view_tickets(db, current_user)
    ticket = _get_visible_ticket(db, ticket_id, current_user)
    if payload.comment_type == "internal" and current_user.role == "requester":
        raise HTTPException(status_code=403, detail="El solicitante no puede crear notas internas")
    comment = TicketComment(ticket_id=ticket.id, author_id=current_user.id, comment_type=payload.comment_type, body=payload.body)
    db.add(comment)
    db.flush()
    write_audit(db, actor=current_user, entity_type="ticket", entity_id=ticket.public_id, action=f"comment_{payload.comment_type}")
    notify_ticket_commented(db, ticket, comment, current_user)
    db.commit()
    return _ticket_to_out(_get_visible_ticket(db, ticket_id, current_user), current_user, db)


@router.get("/{ticket_id}/attachments/{attachment_id}/download")
def download_attachment(ticket_id: str, attachment_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _ensure_can_view_tickets(db, current_user)
    ticket = _get_visible_ticket(db, ticket_id, current_user)
    attachment = db.execute(select(TicketAttachment).where(TicketAttachment.public_id == str(attachment_id))).scalar_one_or_none()
    if not attachment and str(attachment_id).isdigit():
        attachment = db.get(TicketAttachment, int(str(attachment_id)))
    if not attachment or attachment.ticket_id != ticket.id:
        deny_with_audit(db, actor=current_user, entity_type="ticket_attachment", entity_id=str(attachment_id), action="attachment_access_denied")
    if current_user.role == "requester" and attachment.comment and attachment.comment.comment_type == "internal":
        deny_with_audit(db, actor=current_user, entity_type="ticket_attachment", entity_id=attachment.public_id, action="attachment_internal_access_denied")
    file_path = Path(attachment.file_path)
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="Archivo no disponible en el servidor")
    write_audit(db, actor=current_user, entity_type="ticket_attachment", entity_id=attachment.public_id, action="download", new_value=f"{ticket.ticket_number}|{attachment.file_name}")
    db.commit()
    return FileResponse(path=file_path, filename=attachment.file_name, media_type=attachment.content_type or "application/octet-stream")


@router.post("/{ticket_id}/attachments", response_model=TicketOut)
def upload_attachments(
    ticket_id: str,
    files: list[UploadFile] = File(...),
    comment_id: str | None = Form(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_can_view_tickets(db, current_user)
    ticket = _get_visible_ticket(db, ticket_id, current_user)
    comment = None
    if comment_id is not None:
        comment = db.execute(select(TicketComment).where(TicketComment.public_id == str(comment_id))).scalar_one_or_none()
        if not comment and str(comment_id).isdigit():
            comment = db.get(TicketComment, int(str(comment_id)))
        if not comment or comment.ticket_id != ticket.id:
            raise HTTPException(status_code=404, detail="Comentario no encontrado para este ticket")
        if current_user.role == "requester" and comment.comment_type == "internal":
            raise HTTPException(status_code=403, detail="No puedes adjuntar evidencia a una nota interna")
    for file in files:
        original_name, stored_name, size, sha256_hash, detected_mime = _save_upload(file)
        destination = UPLOAD_DIR / stored_name
        db.add(TicketAttachment(
            ticket_id=ticket.id,
            comment_id=comment.id if comment else None,
            uploaded_by_id=current_user.id,
            file_name=original_name,
            stored_name=stored_name,
            file_path=str(destination),
            content_type=file.content_type,
            detected_mime=detected_mime,
            sha256_hash=sha256_hash,
            security_scan_status="validated",
            size_bytes=size,
        ))
    audit_action = "upload_comment_attachment" if comment else "upload_attachment"
    write_audit(db, actor=current_user, entity_type="ticket", entity_id=ticket.public_id, action=audit_action, new_value=f"{len(files)} archivo(s)")
    db.commit()
    return _ticket_to_out(_get_visible_ticket(db, ticket_id, current_user), current_user, db)
