"""
Local, free text embeddings for RAG retrieval - no API key, no per-request
cost, no torch dependency (fastembed uses ONNX runtime, which is much
lighter to install than sentence-transformers). The model itself downloads
once from HuggingFace on first use and is cached in the container/venv.
"""

import logging

logger = logging.getLogger(__name__)

_model = None

MODEL_NAME = "BAAI/bge-small-en-v1.5"  # 384-dim, small, CPU-friendly


def _get_model():
    global _model
    if _model is None:
        from fastembed import TextEmbedding

        _model = TextEmbedding(model_name=MODEL_NAME)
    return _model


def embed_text(text: str) -> list[float] | None:
    """Returns a 384-dim embedding, or None if the model can't be loaded
    (e.g. no internet on first run to download it) - callers should treat
    None as "retrieval unavailable, fall back gracefully", not crash."""
    try:
        embeddings = list(_get_model().embed([text]))
        return embeddings[0].tolist()
    except Exception:
        logger.error("Embedding failed - RAG retrieval will be skipped for this call", exc_info=True)
        return None
