import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class Report(Base):
    """Uploaded lab report file + AI-derived anomaly flags."""

    __tablename__ = "reports"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    booking_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("bookings.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    file_key: Mapped[str] = mapped_column(String(500), nullable=False) 
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    
    extracted_values: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    # AI-flagged anomalies, e.g. [{"parameter": "hemoglobin", "value": 10.2, "normal_range": "13-17", "severity": "low"}]
    anomalies: Mapped[list | None] = mapped_column(JSON, nullable=True)
    # Plain-English summary of the anomalies above, phrased by the LLM - never used to decide severity itself
    ai_explanation: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    # Which reference snippets grounded ai_explanation, e.g. [{"parameter": "hemoglobin", "source_title": "..."}]
    # - lets the patient (or an examiner) see exactly what the explanation was based on, not just trust it.
    explanation_sources: Mapped[list | None] = mapped_column(JSON, nullable=True)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class SymptomQuery(Base):
    """Log of AI symptom -> test recommendations, for personalization/history."""

    __tablename__ = "symptom_queries"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    symptoms_text: Mapped[str] = mapped_column(String(1000), nullable=False)
    recommended_package_ids: Mapped[list | None] = mapped_column(JSON, nullable=True)
    ai_reasoning: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
