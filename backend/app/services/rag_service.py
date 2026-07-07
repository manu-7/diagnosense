"""
Orchestrates the RAG pipeline for anomaly explanations:
  flagged anomaly -> embed a search phrase -> retrieve closest reference
  snippet from Postgres (pgvector cosine similarity) -> pass that specific
  text to the LLM as grounding -> return explanation + which sources it used.

This is intentionally the only place retrieval logic lives, so both the
primary /generate path and the legacy OCR-upload path call the same
function and get identical, groundable behavior.
"""

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.reference_snippet import ReferenceSnippet
from app.services.ai_service import explain_anomalies, explain_anomalies_grounded
from app.services.embedding_service import embed_text

logger = logging.getLogger(__name__)


async def _retrieve_snippet(parameter: str, direction: str, db: AsyncSession) -> ReferenceSnippet | None:
    """Finds the single closest reference snippet for this parameter by
    embedding similarity - not a keyword/exact-match lookup, so phrasing
    differences (e.g. "wbc" vs "white blood cell count") don't matter."""
    query_text = f"{parameter.replace('_', ' ')} {direction} normal range meaning causes"
    query_vector = embed_text(query_text)
    if query_vector is None:
        return None

    stmt = (
        select(ReferenceSnippet)
        .order_by(ReferenceSnippet.embedding.cosine_distance(query_vector))
        .limit(1)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def explain_anomalies_rag(anomalies: list[dict], db: AsyncSession) -> tuple[str, list[dict]]:
    """Full grounded-explanation pipeline. Returns (explanation_text, sources)
    where sources is [{"parameter": ..., "source_title": ...}] - shown to the
    patient so the explanation is checkable, not just trusted.

    Falls back to the ungrounded explain_anomalies() if retrieval finds
    nothing (e.g. embedding model unavailable, or no snippets seeded yet) -
    never blocks or fails the report because RAG infra isn't ready."""
    if not anomalies:
        return "All extracted parameters are within normal reference ranges.", []

    reference_snippets = []
    sources = []
    seen_parameters = set()

    for anomaly in anomalies:
        param = anomaly["parameter"]
        if param in seen_parameters:
            continue
        seen_parameters.add(param)

        snippet = await _retrieve_snippet(param, anomaly.get("direction", ""), db)
        if snippet:
            reference_snippets.append({"parameter": param, "title": snippet.title, "content": snippet.content})
            sources.append({"parameter": param, "source_title": snippet.title})

    if not reference_snippets:
        logger.info("No reference snippets retrieved; falling back to ungrounded explanation.")
        return explain_anomalies(anomalies), []

    explanation = explain_anomalies_grounded(anomalies, reference_snippets)
    return explanation, sources
