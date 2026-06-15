from pydantic import BaseModel, Field


class RequiredQuestionCreate(BaseModel):
    area: str
    severity: str
    category: str = "*"
    question_key: str | None = None
    question_text: str = Field(min_length=3)
    required: bool = True
    sort_order: int = 0
    is_active: bool = True


class RequiredQuestionUpdate(BaseModel):
    area: str | None = None
    severity: str | None = None
    category: str | None = None
    question_key: str | None = None
    question_text: str | None = None
    required: bool | None = None
    sort_order: int | None = None
    is_active: bool | None = None


class RequiredQuestionOut(BaseModel):
    id: int
    area: str
    severity: str
    category: str
    question_key: str
    question_text: str
    required: bool
    sort_order: int
    is_active: bool

    model_config = {"from_attributes": True}
