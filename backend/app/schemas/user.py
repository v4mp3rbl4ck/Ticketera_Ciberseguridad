from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    model_config = {"extra": "forbid"}
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=255)
    password: str = Field(min_length=10)
    role: str = "requester"
    area: str | None = None


class UserUpdate(BaseModel):
    model_config = {"extra": "forbid"}
    full_name: str | None = None
    role: str | None = None
    area: str | None = None
    is_active: bool | None = None
    theme_preference: str | None = None
    new_password: str | None = Field(default=None, min_length=10)


class UserOut(BaseModel):
    id: str
    email: EmailStr
    full_name: str
    role: str
    area: str | None = None
    is_active: bool
    is_deleted: bool = False
    theme_preference: str = "light"
    permissions: dict = Field(default_factory=dict)

    model_config = {"from_attributes": True, "extra": "forbid"}


class UserPasswordReset(BaseModel):
    model_config = {"extra": "forbid"}
    new_password: str = Field(min_length=10)
