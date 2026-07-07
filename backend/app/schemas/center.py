import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class CenterCreate(BaseModel):
    center_name: str = Field(min_length=2, max_length=150)
    address: str = Field(min_length=5, max_length=300)
    city: str = Field(min_length=2, max_length=100)
    license_number: str | None = None


class CenterOut(BaseModel):
    id: uuid.UUID
    center_name: str
    address: str
    city: str
    license_number: str | None
    is_approved: bool
    created_at: datetime

    class Config:
        from_attributes = True
