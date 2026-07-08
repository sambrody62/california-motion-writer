"""
Claim-to-exhibit citation service — inserts "(Exhibit X)" citations inline in
the declaration so each factual claim points at its supporting exhibit.

Zero-drift guardrail: the LLM output with citations stripped must equal the
original text (whitespace/punctuation-normalized), and every cited letter must
be a real exhibit. Any doubt → the original text is used unchanged; workstream
D's authentication paragraphs still enumerate every exhibit, so the filing
stays court-ready on fallback. This function never raises and never blocks
PDF generation.
"""
from __future__ import annotations

import asyncio
import logging
import re
import unicodedata
from typing import List, Optional, Tuple

from app.services import llm_service as llm_backend

logger = logging.getLogger(__name__)

LLM_TIMEOUT_SECONDS = 20
_CITATION_RE = re.compile(r"\s*\(Exhibit [A-Z]{1,2}\)")
_CITED_LETTER_RE = re.compile(r"\(Exhibit ([A-Z]{1,2})\)")


def strip_citations(text: str) -> str:
    return _CITATION_RE.sub("", text)


def _norm(text: str) -> str:
    """Whitespace- and unicode-punctuation-insensitive form for comparison."""
    text = unicodedata.normalize("NFKC", text)
    text = text.replace("‘", "'").replace("’", "'")
    text = text.replace("“", '"').replace("”", '"')
    text = text.replace("–", "-").replace("—", "-")
    return re.sub(r"\s+", " ", text).strip()


def validate_citation_output(original: str, candidate: str, letters: set) -> bool:
    cited = set(_CITED_LETTER_RE.findall(candidate))
    if not cited <= letters:
        return False
    return _norm(strip_citations(candidate)) == _norm(original)


def build_citation_prompt(declaration_text: str, lettered: List[Tuple[str, dict]]) -> str:
    exhibit_lines = []
    for letter_str, item in lettered:
        date_val = item.get("source_date") or "undated"
        desc = (item.get("description") or "")[:200]
        tags = ", ".join(item.get("tags") or [])
        exhibit_lines.append(f"- Exhibit {letter_str}: {item.get('evidence_type', 'document')} "
                             f"dated {date_val} — {desc}" + (f" [tags: {tags}]" if tags else ""))

    return f"""You are inserting exhibit citations into a court declaration. Reproduce the declaration EXACTLY, character for character, changing NOTHING except adding "(Exhibit X)" immediately after sentences that are directly supported by an exhibit below. Cite only clearly supported sentences; when unsure, do not cite.

Exhibits:
{chr(10).join(exhibit_lines)}

Declaration:
---
{declaration_text}
---
Output ONLY the declaration text with citations added. No commentary."""


async def insert_claim_citations(
    declaration_text: str,
    lettered: List[Tuple[str, dict]],
    user_id: Optional[str] = None,
) -> str:
    """Return the declaration with inline citations, or unchanged on any doubt."""
    if not lettered or not declaration_text.strip():
        return declaration_text
    if llm_backend.USE_MOCK_LLM:
        return declaration_text

    try:
        raw, tokens, model = await asyncio.wait_for(
            llm_backend.llm_service._generate(
                build_citation_prompt(declaration_text, lettered),
                "claim_citation",
                user_id,
            ),
            timeout=LLM_TIMEOUT_SECONDS,
        )
    except Exception as exc:
        logger.warning("Claim citation skipped: %s", type(exc).__name__)
        return declaration_text

    letters = {letter_str for letter_str, _ in lettered}
    candidate = raw.strip()
    valid = validate_citation_output(declaration_text, candidate, letters)
    logger.info(
        "Claim citation: input_chars=%d output_chars=%d valid=%s tokens=%s model=%s",
        len(declaration_text), len(candidate), valid, tokens, model,
    )
    return candidate if valid else declaration_text
