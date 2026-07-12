"""
Parse an uploaded served motion (FL-300) into structured facts for pre-filling
the FL-320 response wizard.

The file is read once and discarded — nothing is persisted, and (like
ocr_service) extracted content is never logged, only lengths and flags.

date_served is deliberately excluded end-to-end: it is the date the *user* was
served, which is not in the document, and the 9-court-day response deadline
depends on the user entering it themselves.
"""
import io
import logging
import re
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

import PyPDF2

from app.services import ocr_service
from app.services import llm_service as llm_backend
from app.services.llm_json import parse_llm_json  # noqa: F401  (re-exported for callers/tests)

logger = logging.getLogger(__name__)

NOTICE_MOCK = (
    "Automatic extraction isn't available right now — please type in the "
    "details from the papers you were served."
)
NOTICE_UNREADABLE = (
    "We couldn't read this file. If it's a scanned copy, please type in the "
    "details from the papers you were served."
)
NOTICE_LLM_FAILED = (
    "We couldn't extract the details automatically — please type them in "
    "from the papers you were served."
)

IMAGE_EXTENSIONS = frozenset(["png", "jpg", "jpeg"])
MAX_DOCUMENT_CHARS = 12_000
MAX_REQUESTS_CHARS = 2_000
MIN_TEXT_CHARS = 100  # a text-layer FL-300 has far more; less means scanned/blank

DATE_FORMATS = ["%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y", "%B %d, %Y", "%b %d, %Y"]
TIME_FORMATS = ["%H:%M", "%I:%M %p", "%I:%M%p", "%I %p"]


def extract_pdf_text(content: bytes) -> str:
    """Text layer of a PDF via PyPDF2; empty string on any failure."""
    try:
        reader = PyPDF2.PdfReader(io.BytesIO(content))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    except Exception:
        return ""


def extract_document_text(content: bytes, ext: str) -> Tuple[str, Optional[str]]:
    """(document_text, notice). Empty text always comes with a notice."""
    if ext in IMAGE_EXTENSIONS:
        if ocr_service.ocr_enabled():
            text = ocr_service.extract_text(content)
            if len(text.strip()) >= MIN_TEXT_CHARS:
                return text, None
        return "", NOTICE_UNREADABLE

    text = extract_pdf_text(content)
    if len(text.strip()) < MIN_TEXT_CHARS:
        # No usable text layer — scanned PDFs need the Vision files API,
        # which the current ocr_service does not support
        return "", NOTICE_UNREADABLE
    return text, None


def build_extraction_prompt(document_text: str) -> str:
    return f"""You are reading a California family court Request for Order (FL-300) that was served on the user. Extract only facts that are explicitly present in the document.

Document text:
---
{document_text[:MAX_DOCUMENT_CHARS]}
---

Respond with ONLY a JSON object in this exact format. Use null for anything not explicitly stated — do NOT guess:
{{
    "case_number": "court case number or null",
    "petitioner_name": "name of the party who filed this motion, or null",
    "hearing_date": "hearing date or null",
    "hearing_time": "hearing time or null",
    "other_party_requests": "plain-language summary of every order the filing party is requesting, or null",
    "children": [{{"name": "...", "age": null}}] or null
}}"""


def _normalize_date(value: Any) -> Optional[str]:
    if not isinstance(value, str):
        return None
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(value.strip(), fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


def _normalize_time(value: Any) -> Optional[str]:
    if not isinstance(value, str):
        return None
    cleaned = value.strip().upper().replace("A.M.", "AM").replace("P.M.", "PM")
    for fmt in TIME_FORMATS:
        try:
            return datetime.strptime(cleaned, fmt).strftime("%H:%M")
        except ValueError:
            continue
    return None


def _child_against_document(child: Any, document_text: str) -> Optional[Dict[str, Any]]:
    """Drop children the document never mentions; drop ages not stated near
    the name (finding L3: the extractor invented an 'age 3')."""
    if not isinstance(child, dict):
        return None
    name = str(child.get("name") or "").strip()
    if not name:
        return None
    match = re.search(re.escape(name), document_text, re.IGNORECASE)
    if not match:
        return None
    age = child.get("age")
    if age is None:
        return child
    window = document_text[max(0, match.start() - 40):match.end() + 40]
    if re.search(rf"\b{re.escape(str(age))}\b", window):
        return child
    return {**child, "age": None}


def sanitize_extracted(data: Dict[str, Any], document_text: str = "") -> Dict[str, Any]:
    """Whitelist + normalize LLM output. date_served can never pass through."""
    out: Dict[str, Any] = {}

    for key in ("case_number", "petitioner_name"):
        value = data.get(key)
        if isinstance(value, str) and value.strip():
            out[key] = value.strip()[:200]

    hearing_date = _normalize_date(data.get("hearing_date"))
    if hearing_date:
        out["hearing_date"] = hearing_date

    hearing_time = _normalize_time(data.get("hearing_time"))
    if hearing_time:
        out["hearing_time"] = hearing_time

    requests = data.get("other_party_requests")
    if isinstance(requests, str) and requests.strip():
        out["other_party_requests"] = requests.strip()[:MAX_REQUESTS_CHARS]

    children = data.get("children")
    if isinstance(children, list) and children:
        children = children[:10]
        if document_text:
            children = [
                kept
                for kept in (_child_against_document(c, document_text) for c in children)
                if kept is not None
            ]
        if children:
            out["children"] = children

    return out


async def parse_served_motion(content: bytes, ext: str) -> Dict[str, Any]:
    """{"extracted": {...}, "notice": str | None} — never raises."""
    text, notice = extract_document_text(content, ext)
    if notice:
        return {"extracted": {}, "notice": notice}

    if llm_backend.USE_MOCK_LLM:
        return {"extracted": {}, "notice": NOTICE_MOCK}

    try:
        raw, tokens, model = await llm_backend.llm_service._generate(
            build_extraction_prompt(text), "served_motion_extraction"
        )
    except Exception as exc:
        logger.error("Served-motion extraction failed: %s", type(exc).__name__)
        return {"extracted": {}, "notice": NOTICE_LLM_FAILED}

    extracted = sanitize_extracted(parse_llm_json(raw), text)
    logger.info(
        "Served-motion extraction: doc_chars=%d fields=%d tokens=%s model=%s",
        len(text), len(extracted), tokens, model,
    )
    if not extracted:
        return {"extracted": {}, "notice": NOTICE_LLM_FAILED}
    return {"extracted": extracted, "notice": None}
