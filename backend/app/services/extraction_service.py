"""
Turns an uploaded report file (PDF or scanned image) into structured lab
values, replacing what used to be manual JSON entry by the center.

Two-stage pipeline, deliberately kept separate:
1. extract_text() - mechanical text extraction (pdfplumber for text-based
   PDFs, Tesseract OCR for scanned images). No AI involved, deterministic.
2. parse_lab_values() - a single constrained LLM call that turns messy raw
   text into {parameter: value} JSON. This is the one part that genuinely
   needs AI: report layouts vary too much for regex/positional parsing to
   be worth building, but an LLM handles "Hemoglobin ... 10.2 g/dL" style
   layouts without per-lab templates.

If extraction or parsing fails for any reason (bad scan, unsupported
format, no GROQ key), callers get an empty dict back rather than an
exception - the center can still fall back to the manual /analyze endpoint.
"""

import io
import json
import logging

import pdfplumber
import pytesseract
from PIL import Image

from app.config import settings
from app.services.ai_service import get_client

logger = logging.getLogger(__name__)

PDF_CONTENT_TYPES = {"application/pdf"}
IMAGE_CONTENT_TYPES = {"image/jpeg", "image/jpg", "image/png", "image/webp"}


def extract_text(file_bytes: bytes, content_type: str) -> str:
    """Mechanical extraction only - no AI. Returns "" if the file type isn't
    supported or nothing readable was found, rather than raising."""
    try:
        if content_type in PDF_CONTENT_TYPES:
            text_parts = []
            with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
            text = "\n".join(text_parts).strip()
            if text:
                return text
            # Text-layer PDF extraction found nothing - likely a scanned PDF
            # saved as pages of images. We don't rasterize PDF pages here to
            # keep this dependency-light; images uploaded directly still work.
            logger.warning("No text layer found in uploaded PDF; scanned PDFs need to be uploaded as images.")
            return ""

        if content_type in IMAGE_CONTENT_TYPES:
            image = Image.open(io.BytesIO(file_bytes))
            return pytesseract.image_to_string(image).strip()

        logger.warning("Unsupported content type for extraction: %s", content_type)
        return ""
    except Exception:
        logger.error("Text extraction failed", exc_info=True)
        return ""


def parse_lab_values(raw_text: str) -> dict:
    """Single constrained LLM call: raw OCR/PDF text -> {parameter: value} JSON.
    Grounded strictly to numeric values actually present in the text - told
    explicitly not to infer or invent parameters that aren't there."""
    if not raw_text.strip():
        return {}

    system_prompt = (
        "You extract lab test results from raw report text (which may be messy OCR output). "
        "Return ONLY a JSON object mapping snake_case parameter names to their NUMERIC value, "
        "for example: {\"hemoglobin\": 10.2, \"wbc\": 11200, \"glucose_fasting\": 95}. "
        "Rules: only include values that are explicitly present as numbers in the text - "
        "never invent, estimate, or infer a value that isn't there. Skip units, reference "
        "ranges, and any non-numeric fields. If nothing usable is found, return {}. "
        "Respond with ONLY the JSON object, no markdown, no preamble."
    )

    try:
        response = get_client().chat.completions.create(
            model=settings.GROQ_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": raw_text[:6000]},  # keep well within context limits
            ],
            temperature=0.0,
            max_tokens=800,
        )
        raw = response.choices[0].message.content.strip()
        raw = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        parsed = json.loads(raw)
        return {k: v for k, v in parsed.items() if isinstance(v, (int, float))}
    except Exception:
        logger.error("Lab value parsing failed", exc_info=True)
        return {}


def extract_lab_values_from_file(file_bytes: bytes, content_type: str) -> dict:
    """Full pipeline: file bytes -> raw text -> structured values. Returns {}
    on any failure so the caller can fall back to manual entry instead of
    the whole upload/analysis flow breaking."""
    raw_text = extract_text(file_bytes, content_type)
    if not raw_text:
        return {}
    return parse_lab_values(raw_text)
