"""
Allowed-facts builder — the ground truth the verification passes check
candidates against. Everything derives from what the user actually entered
(intake values, profile addresses, children DOBs); nothing else is allowed.

Date parsing mirrors served_motion_parser.DATE_FORMATS but is reimplemented
locally: the gate is pure stdlib with no cross-service imports.
"""
import re
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, Optional, Set, Tuple

from app.services.fact_gate.authority_strip import address_tokens_from
from app.services.fact_gate.types import GateContext, iter_scalars

DATE_FORMATS = ["%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y", "%B %d, %Y", "%b %d, %Y"]

_MONEY_KEY_HINTS = (
    "amount", "income", "support", "expense", "cost", "fee",
    "wage", "salary", "payment", "arrear", "price", "money",
)
_MONEY_TOKEN_RE = re.compile(r"\$\s?\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?")
_BARE_NUMBER_RE = re.compile(r"\$?\s?\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?|\d+(?:\.\d{1,2})?")

MONTH_WORD = (
    r"(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?"
    r"|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"
)
_MONTH_NUMBERS = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}
_LONG_DATE_RE = re.compile(
    rf"\b{MONTH_WORD}\.?\s+(\d{{1,2}})(?:st|nd|rd|th)?,?\s+(\d{{4}})\b", re.I
)
_YEARLESS_DATE_RE = re.compile(
    rf"\b{MONTH_WORD}\.?\s+(\d{{1,2}})(?:st|nd|rd|th)?\b(?!,?\s*\d{{4}})", re.I
)
_NUMERIC_DATE_RE = re.compile(r"\b(\d{1,2})/(\d{1,2})/(\d{2,4})\b")
_ISO_DATE_RE = re.compile(r"\b(\d{4})-(\d{1,2})-(\d{1,2})\b")


@dataclass
class AllowedFacts:
    """User-entered facts the generated text is allowed to state."""

    amounts: Dict[Decimal, Set[str]] = field(default_factory=dict)  # value -> source keys
    dates: Set[Tuple[int, int, int]] = field(default_factory=set)
    month_days: Set[Tuple[int, int]] = field(default_factory=set)  # year-less entries
    ages: Dict[str, int] = field(default_factory=dict)  # child first name -> age today
    address_tokens: Set[str] = field(default_factory=set)


def month_number(word: str) -> int:
    return _MONTH_NUMBERS[word.lower()[:3]]


def _pivot_year(year: int) -> int:
    if year >= 100:
        return year
    return 2000 + year if year < 70 else 1900 + year


def _money_key(key: str) -> bool:
    lowered = key.lower()
    return any(hint in lowered for hint in _MONEY_KEY_HINTS)


def _add_amount(facts: AllowedFacts, raw: str, key: str) -> None:
    cleaned = raw.replace("$", "").replace(",", "").strip()
    try:
        value = Decimal(cleaned)
    except InvalidOperation:
        return
    facts.amounts.setdefault(value, set()).add(key)


def _add_full_date(facts: AllowedFacts, year: int, month: int, day: int) -> None:
    try:
        date(year, month, day)
    except ValueError:
        return
    facts.dates.add((year, month, day))


def _add_month_day(facts: AllowedFacts, month: int, day: int) -> None:
    try:
        date(2000, month, day)  # leap year: accepts Feb 29
    except ValueError:
        return
    facts.month_days.add((month, day))


def _parse_full_date(value: str) -> Optional[Tuple[int, int, int]]:
    for fmt in DATE_FORMATS:
        try:
            parsed = datetime.strptime(value, fmt)
            return (parsed.year, parsed.month, parsed.day)
        except ValueError:
            continue
    return None


def _collect_amounts_from_text(facts: AllowedFacts, key: str, value: str) -> None:
    for match in _MONEY_TOKEN_RE.finditer(value):
        _add_amount(facts, match.group(), key)
    if _money_key(key) and _BARE_NUMBER_RE.fullmatch(value.strip()):
        _add_amount(facts, value, key)


def _collect_dates_from_text(facts: AllowedFacts, value: str) -> None:
    scalar = _parse_full_date(value.strip())
    if scalar:
        facts.dates.add(scalar)
    for m in _LONG_DATE_RE.finditer(value):
        _add_full_date(facts, int(m.group(3)), month_number(m.group(1)), int(m.group(2)))
    for m in _ISO_DATE_RE.finditer(value):
        _add_full_date(facts, int(m.group(1)), int(m.group(2)), int(m.group(3)))
    for m in _NUMERIC_DATE_RE.finditer(value):
        _add_full_date(facts, _pivot_year(int(m.group(3))), int(m.group(1)), int(m.group(2)))
    for m in _YEARLESS_DATE_RE.finditer(value):
        _add_month_day(facts, month_number(m.group(1)), int(m.group(2)))


def _collect_value(facts: AllowedFacts, key: str, value: Any) -> None:
    if isinstance(value, bool):
        return
    if isinstance(value, (int, float)):
        if _money_key(key):
            _add_amount(facts, str(value), key)
        return
    if isinstance(value, datetime):
        value = value.date()
    if isinstance(value, date):
        _add_full_date(facts, value.year, value.month, value.day)
        return
    if not isinstance(value, str):
        return
    _collect_amounts_from_text(facts, key, value)
    _collect_dates_from_text(facts, value)
    facts.address_tokens |= address_tokens_from(value)


def _child_age(dob: Tuple[int, int, int], today: date) -> Optional[int]:
    year, month, day = dob
    age = today.year - year - ((today.month, today.day) < (month, day))
    return age if 0 <= age <= 120 else None


def _collect_child(facts: AllowedFacts, child: Any, today: date) -> None:
    if not isinstance(child, dict):
        return
    dob_raw = child.get("date_of_birth") or child.get("dob") or child.get("birthdate")
    dob = _parse_full_date(str(dob_raw).strip()) if dob_raw else None
    if not dob:
        return
    facts.dates.add(dob)
    _add_month_day(facts, dob[1], dob[2])
    name = str(child.get("name") or "").strip()
    if not name:
        return
    age = _child_age(dob, today)
    if age is not None:
        facts.ages[name.split()[0].lower()] = age


def build_allowed_facts(ctx: GateContext) -> AllowedFacts:
    facts = AllowedFacts()
    for key, value in iter_scalars(ctx.intake_values):
        _collect_value(facts, key, value)
    today = ctx.today or date.today()
    for child in ctx.children or []:
        _collect_child(facts, child, today)
    for address in ctx.profile_addresses or []:
        if isinstance(address, str):
            facts.address_tokens |= address_tokens_from(address)
    return facts
