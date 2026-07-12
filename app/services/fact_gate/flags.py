"""
Flag-only scans — these NEVER edit the text.

UPL-adjacent advice phrasing gets an upl_flag; quantifier embellishments
("multiple occasions" the user never stated, finding L4) get a
quantifier_flag telling the user to verify the count before signing under
penalty of perjury.
"""
import re
from typing import List, Tuple

from app.services.fact_gate.types import Correction, excerpt, sentence_spans

_UPL_RE = re.compile(
    r"\byou\s+should\s+file\b|\byou\s+should\s+consider\b|\bi\s+recommend\b"
    r"|\bi\s+advise\b|\bwe\s+recommend\b|\byour\s+best\s+option\b"
    r"|\bconsult\s+an\s+attorney\b|\bseek\s+legal\s+advice\b"
    r"|\byou\s+are\s+entitled\s+to\b",
    re.I,
)
_QUANTIFIER_RE = re.compile(
    r"\bmultiple\s+occasions\b|\bseveral\s+times\b|\bnumerous\b|\brepeatedly\b",
    re.I,
)

_UPL_MESSAGE = (
    "This sentence reads like legal advice, which this tool cannot give — "
    "consider rewording it to state facts only."
)


def _sentence_text(text: str, spans: List[Tuple[int, int]], pos: int) -> str:
    for start, end in spans:
        if start <= pos < end:
            return text[start:end]
    return text


def _flag(kind: str, original: str, message: str) -> Correction:
    return Correction(
        type=kind,
        severity="needs_review",
        section="",
        original=excerpt(original),
        replacement=None,
        message=message,
    )


def scan_flags(text: str) -> List[Correction]:
    """Corrections only — the text is returned untouched by the caller."""
    corrections: List[Correction] = []
    spans = sentence_spans(text)
    for match in _UPL_RE.finditer(text):
        corrections.append(
            _flag("upl_flag", _sentence_text(text, spans, match.start()), _UPL_MESSAGE))
    for match in _QUANTIFIER_RE.finditer(text):
        corrections.append(_flag(
            "quantifier_flag",
            _sentence_text(text, spans, match.start()),
            f"The document says \"{match.group()}\" — make sure this count is "
            "accurate before signing under penalty of perjury.",
        ))
    return corrections
