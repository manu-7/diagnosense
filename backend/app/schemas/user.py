import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from app.models.user import UserRole


class UserCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    phone: str | None = None
    password: str = Field(min_length=8, max_length=72)
    role: UserRole = UserRole.PATIENT


class UserOut(BaseModel):
    id: uuid.UUID
    name: str
    email: EmailStr
    phone: str | None
    role: UserRole
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
