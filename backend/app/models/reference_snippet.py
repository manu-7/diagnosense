import uuid

from pgvector.sqlalchemy import Vector
from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base

# bge-small-en-v1.5 (the fastembed default model) produces 384-dim vectors.
EMBEDDING_DIM = 384


class ReferenceSnippet(Base):
    """A short, citable medical reference paragraph for one lab parameter.
    Embedded once at seed time; retrieved by similarity search when an
    anomaly is flagged, so the LLM explains from this specific text instead
    of free-recalling from training data. This is what makes the anomaly
    explanation RAG rather than just an LLM call."""

    __tablename__ = "reference_snippets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    parameter: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)  # shown to the patient as the cited source
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float]] = mapped_column(Vector(EMBEDDING_DIM), nullable=False)
