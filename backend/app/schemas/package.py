import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class PackageCreate(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    description: str | None = None
    symptom_tags: str | None = None
    test_type: str
    price: float = Field(gt=0)


class PackageOut(BaseModel):
    id: uuid.UUID
    center_id: uuid.UUID
    name: str
    description: str | None
    symptom_tags: str | None
    test_type: str
    price: float
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
