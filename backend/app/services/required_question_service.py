import re
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.required_question import RequiredQuestion
from app.schemas.ticket import ChecklistQuestion
from app.services.ticket_catalog_service import get_questions


def make_question_key(text: str, prefix: str = "q") -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "_", text.strip().lower()).strip("_")
    return f"{prefix}_{cleaned[:70]}" if cleaned else f"{prefix}_pregunta"


def get_required_questions(db: Session, area: str, severity: str, category: str | None = None) -> list[ChecklistQuestion]:
    if category:
        category_rows = list(db.execute(
            select(RequiredQuestion)
            .where(
                RequiredQuestion.area == area,
                RequiredQuestion.severity == severity,
                RequiredQuestion.category == category,
                RequiredQuestion.is_active.is_(True),
            )
            .order_by(RequiredQuestion.sort_order, RequiredQuestion.id)
        ).scalars().all())
        if category_rows:
            return [ChecklistQuestion(key=q.question_key, text=q.question_text, required=q.required) for q in category_rows]

    generic_rows = list(db.execute(
        select(RequiredQuestion)
        .where(
            RequiredQuestion.area == area,
            RequiredQuestion.severity == severity,
            RequiredQuestion.category == "*",
            RequiredQuestion.is_active.is_(True),
        )
        .order_by(RequiredQuestion.sort_order, RequiredQuestion.id)
    ).scalars().all())
    if generic_rows:
        return [ChecklistQuestion(key=q.question_key, text=q.question_text, required=q.required) for q in generic_rows]

    return [ChecklistQuestion(key=key, text=text, required=True) for key, text in get_questions(area, severity)]
