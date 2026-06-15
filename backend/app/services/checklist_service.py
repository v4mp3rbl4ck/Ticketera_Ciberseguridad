from app.schemas.ticket import ChecklistQuestion
from app.services.ticket_catalog_service import get_questions


def get_checklist(area: str, severity: str) -> list[ChecklistQuestion]:
    return [ChecklistQuestion(key=key, text=text, required=True) for key, text in get_questions(area, severity)]
