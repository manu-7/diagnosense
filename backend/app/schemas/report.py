import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class GenerateReportRequest(BaseModel):
    extracted_values: dict = Field(
        description='Lab values the center enters directly, e.g. {"hemoglobin": 10.2, "wbc": 12500}'
    )


class ReportOut(BaseModel):
    id: uuid.UUID
    booking_id: uuid.UUID
    original_filename: str
    extracted_values: dict | None
    anomalies: list | None
    ai_explanation: str | None = None
    explanation_sources: list | None = None
    uploaded_at: datetime

    class Config:
        from_attributes = True


class ReportDownloadOut(BaseModel):
    signed_url: str
    expires_in_seconds: int


class SymptomCheckRequest(BaseModel):
    symptoms: str = Field(min_length=3, max_length=1000, description="Free-text description of symptoms")
    city: str | None = Field(default=None, description="Optional city filter for recommended centers")


class RecommendedPackage(BaseModel):
    package_id: uuid.UUID
    name: str
    center_name: str
    test_type: str
    price: float
    match_reason: str


class SymptomCheckResponse(BaseModel):
    recommended_packages: list[RecommendedPackage]
    ai_reasoning: str
    disclaimer: str = (
        "This is an automated suggestion based on described symptoms and is not a medical diagnosis. "
        "Please consult a licensed physician for medical advice."
    )
