from pydantic import BaseModel, EmailStr, Field


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginResponse(Token):
    user: "UserOut"


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


LoginResponse.model_rebuild()


class PasswordChange(BaseModel):
    current_password: str
    new_password: str


class ProfileUpdate(BaseModel):
    full_name: str | None = None
    theme_preference: str | None = None
