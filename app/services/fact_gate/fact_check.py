"""
Amount, date, and age verification against AllowedFacts.

- Amounts (finding L2): only $-prefixed tokens are candidates. Unknown
  amounts become [TO BE COMPLETED]; a support-sentence amount sourced only
  from income answers is blocked the same way.
- Dates (finding L4): long-form/numeric/ISO singles and month-day ranges;
  ranges are trimmed to the endpoints the user actually entered.
- Ages (finding L3): computed from children DOBs; numbers are paired with
  the nearest child name in the sentence and corrected in place.
"""
import re
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import List, Optional, Tuple

from app.services.fact_gate.allowed_facts import AllowedFacts, MONTH_WORD, month_number
from app.services.fact_gate.types import Correction, excerpt, sentence_spans

PLACEHOLDER = "[TO BE COMPLETED]"

_AMOUNT_TOKEN_RE = re.compile(r"\$\s?\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?")
_SUPPORT_CONTEXT_RE = re.compile(r"(?:child|spousal)\s+support", re.I)

_RANGE_RE = re.compile(
    rf"\b{MONTH_WORD}\.?\s+(\d{{1,2}})\s*[–—-]\s*(\d{{1,2}})(?:,\s*(\d{{4}}))?\b", re.I
)
_LONG_DATE_RE = re.compile(
    rf"\b{MONTH_WORD}\.?\s+(\d{{1,2}})(?:st|nd|rd|th)?,?\s+(\d{{4}})\b", re.I
)
_NUMERIC_DATE_RE = re.compile(r"\b(\d{1,2})/(\d{1,2})/(\d{2,4})\b")
_ISO_DATE_RE = re.compile(r"\b(\d{4})-(\d{1,2})-(\d{1,2})\b")

_AGE_WORD_RE = re.compile(r"\baged?\s+(\d{1,2})\b", re.I)
_YEARS_OLD_RE = re.compile(r"\b(\d{1,2})\s+years?\s+old\b", re.I)
_BARE_YEARS_RE = re.compile(r"\b(\d{1,2})\s+years\b(?!\s+old)", re.I)
_DURATION_GUARD_RE = re.compile(
    r"\b(?:for|past|last|over|about|approximately|nearly|than|within)\s*$", re.I
)

_UNKNOWN_AMOUNT_MSG = (
    "This dollar amount doesn't match anything you entered — please fill in the correct figure."
)
_INCOME_AS_SUPPORT_MSG = (
    "This amount came from your income answer, not a support request — please review."
)
_UNKNOWN_DATE_MSG = "This date doesn't match any date you entered — please verify it before filing."
_TRIMMED_RANGE_MSG = (
    "This date range included a day you didn't enter, so it was shortened to the date you gave."
)
_UNMATCHED_AGE_MSG = (
    "An age is mentioned that we couldn't match to a specific child — "
    "please verify it against the dates of birth."
)


def _apply(text: str, replacements: List[Tuple[int, int, str]]) -> str:
    for start, end, replacement in sorted(replacements, reverse=True):
        text = text[:start] + replacement + text[end:]
    return text


def _sentence_at(spans: List[Tuple[int, int]], pos: int) -> Tuple[int, int]:
    for start, end in spans:
        if start <= pos < end:
            return start, end
    return 0, 0


def _correction(kind: str, severity: str, original: str, replacement: Optional[str],
                message: str) -> Correction:
    return Correction(type=kind, severity=severity, section="",
                      original=excerpt(original), replacement=replacement, message=message)


def _amount_issue(sources: Optional[set], sentence: str) -> Optional[str]:
    if sources is None:
        return _UNKNOWN_AMOUNT_MSG
    if not _SUPPORT_CONTEXT_RE.search(sentence):
        return None
    keys = {key.lower() for key in sources}
    if any("support" in key for key in keys):
        return None
    if keys and all("income" in key for key in keys):
        return _INCOME_AS_SUPPORT_MSG
    return None


def check_amounts(text: str, facts: AllowedFacts) -> Tuple[str, List[Correction]]:
    """$-prefixed tokens must be user-entered and support-sourced in support sentences."""
    corrections: List[Correction] = []
    replacements: List[Tuple[int, int, str]] = []
    spans = sentence_spans(text)
    for match in _AMOUNT_TOKEN_RE.finditer(text):
        try:
            value = Decimal(match.group().replace("$", "").replace(",", "").strip())
        except InvalidOperation:
            continue
        start, end = _sentence_at(spans, match.start())
        issue = _amount_issue(facts.amounts.get(value), text[start:end])
        if issue:
            replacements.append((match.start(), match.end(), PLACEHOLDER))
            corrections.append(
                _correction("amount", "needs_review", match.group(), PLACEHOLDER, issue))
    return _apply(text, replacements), corrections


def _pivot_year(year: int) -> int:
    if year >= 100:
        return year
    return 2000 + year if year < 70 else 1900 + year


def _date_allowed(year: Optional[int], month: int, day: int, facts: AllowedFacts) -> Optional[bool]:
    """True/False for real dates; None when (month, day) is not a real date."""
    try:
        date(year if year else 2000, month, day)
    except ValueError:
        return None
    if year:
        return (year, month, day) in facts.dates or (month, day) in facts.month_days
    if (month, day) in facts.month_days:
        return True
    return any((m, d) == (month, day) for (_, m, d) in facts.dates)


def _range_replacement(match: re.Match, facts: AllowedFacts) -> Tuple[Optional[str], str]:
    month_word = match.group(1)
    day_one, day_two = int(match.group(2)), int(match.group(3))
    year = int(match.group(4)) if match.group(4) else None
    month = month_number(month_word)
    allowed_one = _date_allowed(year, month, day_one, facts)
    allowed_two = _date_allowed(year, month, day_two, facts)
    if allowed_one is None or allowed_two is None or (allowed_one and allowed_two):
        return None, ""

    def fmt(day: int) -> str:
        return f"{month_word} {day}, {year}" if year else f"{month_word} {day}"

    if allowed_one:
        return fmt(day_one), _TRIMMED_RANGE_MSG
    if allowed_two:
        return fmt(day_two), _TRIMMED_RANGE_MSG
    return PLACEHOLDER, _UNKNOWN_DATE_MSG


def _single_date_candidates(text: str):
    for match in _LONG_DATE_RE.finditer(text):
        yield match, (int(match.group(3)), month_number(match.group(1)), int(match.group(2)))
    for match in _ISO_DATE_RE.finditer(text):
        yield match, (int(match.group(1)), int(match.group(2)), int(match.group(3)))
    for match in _NUMERIC_DATE_RE.finditer(text):
        yield match, (_pivot_year(int(match.group(3))), int(match.group(1)), int(match.group(2)))


def check_dates(text: str, facts: AllowedFacts) -> Tuple[str, List[Correction]]:
    """Verify date mentions; trim ranges to entered endpoints; block unknowns."""
    corrections: List[Correction] = []
    replacements: List[Tuple[int, int, str]] = []
    occupied: List[Tuple[int, int]] = []
    for match in _RANGE_RE.finditer(text):
        occupied.append((match.start(), match.end()))
        replacement, message = _range_replacement(match, facts)
        if replacement is not None:
            replacements.append((match.start(), match.end(), replacement))
            corrections.append(
                _correction("date", "needs_review", match.group(), replacement, message))
    for match, ymd in _single_date_candidates(text):
        if any(match.start() < end and match.end() > start for start, end in occupied):
            continue
        if _date_allowed(*ymd, facts) is False:
            replacements.append((match.start(), match.end(), PLACEHOLDER))
            corrections.append(_correction(
                "date", "needs_review", match.group(), PLACEHOLDER, _UNKNOWN_DATE_MSG))
    return _apply(text, replacements), corrections


def _age_candidates(sentence: str, bound_rx: Optional[re.Pattern]):
    """(num_start, num_end, value, kind, bound_name) candidates in a sentence."""
    seen = set()

    def add(match: re.Match, kind: str, bound_name: Optional[str] = None):
        span = (match.start(1) if bound_name is None else match.start(2),
                match.end(1) if bound_name is None else match.end(2))
        if span in seen:
            return
        seen.add(span)
        value = int(match.group(1) if bound_name is None else match.group(2))
        candidates.append((span[0], span[1], value, kind, bound_name))

    candidates: List[Tuple[int, int, int, str, Optional[str]]] = []
    if bound_rx:
        for match in bound_rx.finditer(sentence):
            add(match, "age", match.group(1).lower())
    for match in _AGE_WORD_RE.finditer(sentence):
        add(match, "age")
    for match in _YEARS_OLD_RE.finditer(sentence):
        add(match, "age")
    for match in _BARE_YEARS_RE.finditer(sentence):
        if not _DURATION_GUARD_RE.search(sentence[:match.start()]):
            add(match, "years")
    return candidates


def _expected_age(names: List[Tuple[int, str]], pos: int, kind: str, value: int,
                  facts: AllowedFacts) -> Tuple[Optional[int], bool]:
    """(expected age, flag_only). Nearest-preceding name wins, else following."""
    if names:
        preceding = [item for item in names if item[0] <= pos]
        chosen = max(preceding)[1] if preceding else min(n for n in names if n[0] > pos)[1]
        return facts.ages.get(chosen), False
    if kind != "age" or value > 17:
        return None, False
    if len(facts.ages) == 1:
        return next(iter(facts.ages.values())), False
    return None, True


def check_ages(text: str, facts: AllowedFacts) -> Tuple[str, List[Correction]]:
    """Correct stated child ages against DOB-derived truth."""
    if not facts.ages:
        return text, []
    names_alt = "|".join(re.escape(name) for name in sorted(facts.ages))
    names_rx = re.compile(rf"\b({names_alt})\b", re.I)
    bound_rx = re.compile(rf"\b({names_alt})\s*\(\s*(\d{{1,2}})\s*\)", re.I)
    corrections: List[Correction] = []
    replacements: List[Tuple[int, int, str]] = []
    for start, end in sentence_spans(text):
        sentence = text[start:end]
        names = [(m.start(), m.group(1).lower()) for m in names_rx.finditer(sentence)]
        for num_start, num_end, value, kind, bound in _age_candidates(sentence, bound_rx):
            if bound:
                expected, flag_only = facts.ages.get(bound), False
            else:
                expected, flag_only = _expected_age(names, num_start, kind, value, facts)
            if flag_only:
                corrections.append(_correction(
                    "age", "needs_review", sentence, None, _UNMATCHED_AGE_MSG))
            elif expected is not None and expected != value:
                replacements.append((start + num_start, start + num_end, str(expected)))
                corrections.append(_correction(
                    "age", "corrected", text[start + num_start:start + num_end],
                    str(expected),
                    "An age was corrected using the child's date of birth.",
                ))
    return _apply(text, replacements), corrections
