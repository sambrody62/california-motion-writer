"""
OCR service — env-gated Cloud Vision transcription suggestions.

Feature flag: OCR_ENABLED=true enables this service.
The google-cloud-vision lib is imported conditionally so the module loads
cleanly even when the package is absent or the flag is off.
"""
import logging
import os

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Conditional import — mirrors the pattern in llm_service.py
# ---------------------------------------------------------------------------
try:
    from google.cloud import vision as _vision_lib
    _VISION_AVAILABLE = True
except ImportError:  # pragma: no cover
    _VISION_AVAILABLE = False


def ocr_enabled() -> bool:
    """Return True only when OCR_ENABLED=true AND the vision lib is present."""
    return (
        os.getenv("OCR_ENABLED", "false").lower() == "true"
        and _VISION_AVAILABLE
    )


def _build_vision_client():
    """Construct a Cloud Vision ImageAnnotatorClient. Extracted for easy mocking."""
    return _vision_lib.ImageAnnotatorClient()


def extract_text(image_bytes: bytes) -> str:
    """Run Cloud Vision document_text_detection on image_bytes.

    Returns the extracted text string, or "" on any error.
    Never raises — caller is in the request path.
    PII-safe: we never log the transcription content, only error messages.
    """
    if not _VISION_AVAILABLE:
        return ""

    try:
        client = _build_vision_client()
        image = _vision_lib.Image(content=image_bytes)
        response = client.document_text_detection(image=image)
        return response.full_text_annotation.text or ""
    except Exception:
        logger.exception("OCR extraction failed")
        return ""
