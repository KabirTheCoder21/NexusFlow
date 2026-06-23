from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from src.user.enums import UserRole


class CreateUserDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(..., min_length=2, max_length=20)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=128)


class LoginDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: EmailStr
    password: str


class UserResponseDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    email: EmailStr
    role: UserRole
    is_active: bool

    created_at: datetime
    updated_at: datetime


class UpdateUserDTO(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=20)
    email: EmailStr | None = None


class ChangePasswordDTO(BaseModel):

    old_password: str = Field(min_length=6, max_length=128)

    new_password: str = Field(min_length=8, max_length=128)


class MessageResponseDTO(BaseModel):
    message: str
