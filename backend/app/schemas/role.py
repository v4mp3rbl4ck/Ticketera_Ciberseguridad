from datetime import datetime
from pydantic import BaseModel, Field


class RolePermissionIn(BaseModel):
    module_key: str
    can_view: bool = False
    can_create: bool = False
    can_edit: bool = False
    can_delete: bool = False


class RolePermissionOut(RolePermissionIn):
    id: int | None = None

    model_config = {"from_attributes": True}


class RoleCreate(BaseModel):
    key: str = Field(min_length=2, max_length=80, pattern=r"^[a-zA-Z0-9_-]+$")
    name: str = Field(min_length=2, max_length=120)
    description: str | None = None
    is_active: bool = True
    permissions: list[RolePermissionIn] = []


class RoleUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    is_active: bool | None = None
    permissions: list[RolePermissionIn] | None = None


class RoleOut(BaseModel):
    id: int
    key: str
    name: str
    description: str | None = None
    is_system: bool
    is_active: bool
    created_at: datetime
    permissions: list[RolePermissionOut] = []

    model_config = {"from_attributes": True}


class RoleModuleOut(BaseModel):
    key: str
    label: str
    description: str
    group: str
