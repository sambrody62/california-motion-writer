"""
Legal-authority stripper (finding L7): the LLM invented statutes, local
rules, case law, courthouse addresses, and FL-150/earnings-assignment
instructions. All of it is unverifiable, so it is removed — narrowly:

- citation inside a parenthetical  -> the whole parenthetical goes
- citation after a connector       -> connector + citation go
- otherwise                        -> the citation goes; a sentence left
  with fewer than 4 words goes entirely
- street-address and support-paperwork sentences go whole, but ONLY when
  the address has no token overlap with user-entered locations / ONLY
  when no support was requested.

Every removal produces a needs_review Correction quoting the removed text.
"""
import re
from typing import List, Optional, Set, Tuple

from app.services.fact_gate.types import (
    Correction,
    GateContext,
    excerpt,
    iter_scalars,
    sentence_spans,
)

_MARK = "\x00"  # placed at removal sites so the short-sentence rule can see them

_SECTION_NUM = r"\d+(?:\.\d+)*(?:\([a-zA-Z0-9]+\))*"
_CASE_TAIL = r"(?:\s*\(\d{4}\))?(?:\s*\d+\s+Cal\.(?:\s?App\.)?\s?\d*(?:st|nd|rd|th|d)?\s+\d+)?"
_CITATION_RES = [
    re.compile(
        rf"\b(?:Family|Civil|Penal|Evidence|Welfare\s+and\s+Institutions)\s+Code,?"
        rf"\s+(?:sections?|§§?)\s*{_SECTION_NUM}",
        re.I,
    ),
    re.compile(rf"\b(?:Fam|Civ|Pen|Evid)\.?\s+Code,?\s+(?:sections?|§§?)\s*{_SECTION_NUM}", re.I),
    re.compile(rf"\bCode\s+of\s+Civil\s+Procedure,?\s+(?:sections?|§§?)\s*{_SECTION_NUM}", re.I),
    re.compile(rf"\bCalifornia\s+Rules\s+of\s+Court,?\s+rules?\s+{_SECTION_NUM}", re.I),
    re.compile(
        r"\b(?:(?:[A-Z][A-Za-z]+\s+){0,3}Superior\s+Court\s+)?"
        r"[Ll]ocal\s+[Rr]ules?\s+(?:No\.\s*)?\d[\d.]*"
    ),
    re.compile(
        rf"\bIn\s+re\s+(?:the\s+)?(?:Marriage\s+of\s+)?[A-Z][A-Za-z'’-]+{_CASE_TAIL}"
    ),
    re.compile(rf"\b[A-Z][A-Za-z'’-]+\s+v\.\s+[A-Z][A-Za-z'’-]+{_CASE_TAIL}"),
]
_PAREN_RE = re.compile(r"\([^()]*\)")
_CONNECTOR_RE = re.compile(r"(?:pursuant\s+to|under|;\s*see(?:\s+also)?|,?\s*citing)[\s(]*$", re.I)

_STREET_SUFFIX = r"(?:Street|Avenue|Boulevard|Drive|Road|Lane|Way|St|Ave|Blvd|Dr|Rd|Ln)"
_ADDRESS_RE = re.compile(rf"\b\d{{2,5}}\s+(?:[A-Z][A-Za-z'.]*\s+){{1,4}}{_STREET_SUFFIX}\b")
_LOOSE_STREET_RE = re.compile(rf"\b(?:\d{{1,5}}\s+)?(?:[A-Z][A-Za-z'.]*\s+){{1,4}}{_STREET_SUFFIX}\b")
_GENERIC_TOKENS = frozenset({
    "street", "avenue", "boulevard", "drive", "road", "lane", "way",
    "ave", "blvd", "the", "and", "near", "suite", "ste", "apt", "unit",
    "north", "south", "east", "west",
})

_SUPPORT_DOC_RE = re.compile(
    r"\bFL-150\b|\bIncome\s+and\s+Expense\s+Declaration\b"
    r"|\bearnings\s+assignment\b|\bwage\s+assignment\b",
    re.I,
)

_CITATION_MESSAGE = (
    "A legal citation was removed because it was generated automatically and "
    "could not be verified. Do not cite legal authority you have not checked yourself."
)
_ADDRESS_MESSAGE = (
    "This sentence contained a street address that does not match anything you "
    "entered, so it was removed."
)
_SUPPORT_DOC_MESSAGE = (
    "This sentence about support paperwork was removed because your answers "
    "did not request child or spousal support."
)
_HUSK_MESSAGE = "The rest of this sentence was removed because it only introduced a citation."


def _tokens(fragment: str) -> Set[str]:
    return {
        word
        for word in re.findall(r"[a-z']+", fragment.lower())
        if len(word) >= 3 and word not in _GENERIC_TOKENS
    }


def address_tokens_from(text: str) -> Set[str]:
    """Normalized street-name tokens found in user-entered text."""
    tokens: Set[str] = set()
    for match in _LOOSE_STREET_RE.finditer(text):
        tokens |= _tokens(match.group())
    return tokens


def _support_requested(ctx: GateContext) -> bool:
    for key, value in iter_scalars(ctx.intake_values):
        if "support" in key.lower() and str(value).strip():
            return True
    return False


def _word_count(text: str) -> int:
    return len(re.findall(r"[A-Za-z]+", text))


def _merge_spans(spans: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
    merged: List[Tuple[int, int]] = []
    for start, end in sorted(spans):
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(end, merged[-1][1]))
        else:
            merged.append((start, end))
    return merged


def _expand_span(text: str, start: int, end: int) -> Tuple[int, int]:
    """Widen a citation span to its parenthetical or leading connector."""
    for match in _PAREN_RE.finditer(text):
        if match.start() <= start and end <= match.end():
            return match.start(), match.end()
    lookback = text[max(0, start - 30):start]
    match = _CONNECTOR_RE.search(lookback)
    if match:
        return start - (len(lookback) - match.start()), end
    return start, end


def _removal(removed_text: str, message: str) -> Correction:
    return Correction(
        type="authority_removed",
        severity="needs_review",
        section="",
        original=excerpt(removed_text),
        replacement=None,
        message=message,
    )


def _remove_citations(text: str, corrections: List[Correction]) -> str:
    raw = [(m.start(), m.end()) for rx in _CITATION_RES for m in rx.finditer(text)]
    expanded = [_expand_span(text, start, end) for start, end in _merge_spans(raw)]
    for start, end in reversed(_merge_spans(expanded)):
        corrections.append(_removal(text[start:end], _CITATION_MESSAGE))
        text = text[:start] + _MARK + text[end:]
    return text


def _sentence_removal_reason(
    sentence: str, allowed_tokens: Set[str], support_ok: bool
) -> Optional[str]:
    for match in _ADDRESS_RE.finditer(sentence):
        if not (_tokens(match.group()) & allowed_tokens):
            return _ADDRESS_MESSAGE
    if not support_ok and _SUPPORT_DOC_RE.search(sentence):
        return _SUPPORT_DOC_MESSAGE
    if _MARK in sentence and _word_count(sentence) < 4:
        return _HUSK_MESSAGE
    return None


def _remove_sentences(
    text: str, allowed_tokens: Set[str], ctx: GateContext, corrections: List[Correction]
) -> str:
    support_ok = _support_requested(ctx)
    removals = []
    for start, end in sentence_spans(text):
        reason = _sentence_removal_reason(text[start:end], allowed_tokens, support_ok)
        if reason:
            removals.append((start, end, reason))
    for start, end, reason in reversed(removals):
        clean = text[start:end].replace(_MARK, "")
        if re.search(r"[A-Za-z]", clean):
            corrections.append(_removal(clean, reason))
        while end < len(text) and text[end] in " \t":
            end += 1
        text = text[:start] + text[end:]
    return text


def _tidy(text: str) -> str:
    text = text.replace(_MARK, "")
    text = re.sub(r"\(\s*\)", "", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r" ([.,;:!?])", r"\1", text)
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text


def strip_authority(
    text: str, allowed_address_tokens: Set[str], ctx: GateContext
) -> Tuple[str, List[Correction]]:
    """Remove unverifiable legal authority; every removal is a Correction."""
    original = text
    corrections: List[Correction] = []
    text = _remove_citations(text, corrections)
    text = _remove_sentences(text, allowed_address_tokens, ctx, corrections)
    if not corrections:
        return original, []
    return _tidy(text), corrections
