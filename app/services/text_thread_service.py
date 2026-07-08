"""
Text-thread service — merges OCR extractions from multiple text-message
screenshots into one chronological conversation transcript.

The transcript is a *suggestion*: the user reviews and edits it before it is
saved as Evidence. Nothing here persists anything, and (per the PII rule)
extracted content is never logged — only lengths and flags.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from app.services import llm_service as llm_backend
from app.services.llm_json import parse_llm_json
from app.services.served_motion_parser import _normalize_date

logger = logging.getLogger(__name__)

NOTICE_MOCK = (
    "Automatic merging isn't available right now — the screenshots were "
    "combined in upload order. Please review and fix the order before saving."
)
NOTICE_LLM_FAILED = (
    "We couldn't merge the screenshots automatically — they were combined in "
    "upload order. Please review and fix the order before saving."
)
NOTICE_NO_TEXT = (
    "We couldn't read any text from these images. Please type the conversation "
    "in yourself, or try clearer screenshots."
)

MAX_CHARS_PER_IMAGE = 4_000
MAX_TOTAL_CHARS = 30_000
_MAX_PARTICIPANTS = 10


def concat_fallback(ocr_texts: List[Dict[str, str]]) -> str:
    """Header-separated concatenation in upload order — always usable."""
    blocks = [
        f"--- {entry['filename']} ---\n{entry['text'].strip()}"
        for entry in ocr_texts
    ]
    return "\n\n".join(blocks)


def build_threading_prompt(ocr_texts: List[Dict[str, str]]) -> str:
    total = 0
    sections = []
    for i, entry in enumerate(ocr_texts, start=1):
        text = entry["text"][:MAX_CHARS_PER_IMAGE]
        total += len(text)
        if total > MAX_TOTAL_CHARS:
            break
        sections.append(f"Screenshot {i} ({entry['filename']}):\n---\n{text}\n---")

    return f"""These are OCR extractions from screenshots of one text-message conversation, possibly out of order and with overlapping messages. Merge them into ONE chronological transcript. Rules: use only text present in the extractions — never invent messages; drop duplicated messages from overlapping screenshots; format each message as "[YYYY-MM-DD HH:MM] Sender: message" when date/time is visible, otherwise "Sender: message"; keep original wording exactly.

{chr(10).join(sections)}

Respond with ONLY JSON:
{{"transcript": "...", "participants": ["..."], "date_start": "YYYY-MM-DD or null", "date_end": "YYYY-MM-DD or null"}}"""


def _sanitize(parsed: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    transcript = parsed.get("transcript")
    if not isinstance(transcript, str) or not transcript.strip():
        return None
    participants = [
        p[:100] for p in (parsed.get("participants") or [])
        if isinstance(p, str) and p.strip()
    ][:_MAX_PARTICIPANTS]
    date_start = _normalize_date(parsed.get("date_start"))
    date_end = _normalize_date(parsed.get("date_end"))
    return {
        "merged_transcript": transcript.strip(),
        "participants": participants,
        "date_range": {"start": date_start, "end": date_end},
        "suggested_source_date": date_start,
    }


def _fallback(ocr_texts: List[Dict[str, str]], notice: str) -> Dict[str, Any]:
    return {
        "merged_transcript": concat_fallback(ocr_texts),
        "participants": [],
        "date_range": {"start": None, "end": None},
        "suggested_source_date": None,
        "notice": notice,
        "used_llm": False,
    }


def build_vision_prompt(n_images: int) -> str:
    return f"""These are {n_images} screenshots of one text-message conversation, possibly out of order and with overlapping messages. Read them and merge into ONE chronological transcript. Rules: right-aligned bubbles are messages FROM the user — call that sender "Me" unless a name is visible; left-aligned bubbles are from the other party (use the name shown at the top of the chat if visible); use only text visible in the screenshots — never invent messages; drop duplicated messages from overlapping screenshots; format each message as "[YYYY-MM-DD HH:MM] Sender: message" when a date/time is visible, otherwise "Sender: message"; keep original wording exactly.

Respond with ONLY JSON:
{{"transcript": "...", "participants": ["..."], "date_start": "YYYY-MM-DD or null", "date_end": "YYYY-MM-DD or null"}}"""


async def read_screenshot_images(
    images: List[Dict[str, Any]],
    user_id: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Read chat screenshots directly with Claude vision.

    images: [{"filename": str, "content": bytes, "media_type": str}].
    Returns the thread_screenshots() result shape on success, or None on any
    failure — the caller falls through to the OCR path. Never raises.
    """
    backend = getattr(llm_backend.llm_service, "claude_backend", None)
    if llm_backend.USE_MOCK_LLM or backend is None or not images:
        return None

    try:
        raw, tokens, model = await backend.generate_with_images(
            build_vision_prompt(len(images)),
            [(img["content"], img["media_type"]) for img in images],
            "screenshot_reading",
            user_id,
        )
    except Exception as exc:
        logger.warning("Screenshot vision reading failed: %s", type(exc).__name__)
        return None

    sanitized = _sanitize(parse_llm_json(raw))
    if sanitized is None:
        logger.warning("Screenshot vision reading returned unusable output")
        return None

    logger.info(
        "Screenshot vision: images=%d transcript_chars=%d tokens=%s model=%s",
        len(images), len(sanitized["merged_transcript"]), tokens, model,
    )
    return {**sanitized, "notice": None, "used_llm": True}


async def thread_screenshots(
    ocr_texts: List[Dict[str, str]],
    user_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Merge OCR extractions into one transcript; never raises."""
    if llm_backend.USE_MOCK_LLM:
        return _fallback(ocr_texts, NOTICE_MOCK)

    try:
        raw, tokens, model = await llm_backend.llm_service._generate(
            build_threading_prompt(ocr_texts), "conversation_threading", user_id
        )
    except Exception as exc:
        logger.warning("Screenshot threading failed: %s", type(exc).__name__)
        return _fallback(ocr_texts, NOTICE_LLM_FAILED)

    sanitized = _sanitize(parse_llm_json(raw))
    if sanitized is None:
        return _fallback(ocr_texts, NOTICE_LLM_FAILED)

    logger.info(
        "Screenshot threading: images=%d transcript_chars=%d tokens=%s model=%s",
        len(ocr_texts), len(sanitized["merged_transcript"]), tokens, model,
    )
    return {**sanitized, "notice": None, "used_llm": True}
