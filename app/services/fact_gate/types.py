"""
Dataclasses and shared plumbing for the fact-fidelity gate.

Correction messages are shown to users verbatim, so they are plain English.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date
from typing import Any, Dict, Iterator, List, Optional, Tuple

EXCERPT_LIMIT = 120


@dataclass
class GateContext:
    """Everything the gate is allowed to treat as ground truth."""

    motion_kind: str = "rfo_section"  # rfo_section | response_section | declaration
    section_name: str = ""
    party_name: str = ""
    other_party_name: str = ""
    is_petitioner: bool = True
    case_number: str = ""
    county: str = ""
    # [{"name": ..., "date_of_birth"|"dob"|"birthdate": ...}, ...]
    children: List[Dict[str, Any]] = field(default_factory=list)
    # merged question_data/intake_data
    intake_values: Dict[str, Any] = field(default_factory=dict)
    profile_addresses: List[str] = field(default_factory=list)
    today: Optional[date] = None  # injectable for deterministic age tests


@dataclass
class Correction:
    """One correction or flag produced by a gate pass."""

    # markdown | authority_removed | placeholder_filled | party_role |
    # amount | date | age | upl_flag | quantifier_flag
    type: str
    severity: str  # corrected | needs_review | info
    section: str
    original: str  # excerpt of the affected text, <=120 chars
    replacement: Optional[str]
    message: str

    def as_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "severity": self.severity,
            "section": self.section,
            "original": self.original,
            "replacement": self.replacement,
            "message": self.message,
        }


@dataclass
class GateResult:
    text: str
    corrections: List[Correction] = field(default_factory=list)

    def as_report(self) -> Dict[str, Any]:
        return {"version": 1, "corrections": [c.as_dict() for c in self.corrections]}


def excerpt(text: str, limit: int = EXCERPT_LIMIT) -> str:
    """Whitespace-collapsed excerpt for Correction.original."""
    text = " ".join(text.split())
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def _is_blank(value: Any) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def merge_intake_values(dicts: List[Any]) -> Dict[str, Any]:
    """Merge per-step intake dicts in order, ignoring blank re-registrations.

    The intake wizard saves each step with the raw form store, so later steps
    re-register earlier fields as None/""/all-false (871cafa family). Blanks
    never overwrite real answers; checkbox groups union their truthy leaves;
    a genuine non-blank re-answer on a later step still wins.
    """
    merged: Dict[str, Any] = {}
    for data in dicts:
        if not isinstance(data, dict):
            continue
        for key, value in data.items():
            if _is_blank(value):
                continue
            if isinstance(value, dict):
                truthy = {k: v for k, v in value.items() if v}
                if not truthy:
                    continue
                existing = merged.get(key)
                merged[key] = (
                    {**existing, **truthy} if isinstance(existing, dict) else truthy
                )
                continue
            merged[key] = value
    return merged


def iter_scalars(value: Any, key: str = "") -> Iterator[Tuple[str, Any]]:
    """Yield (key, scalar) pairs from arbitrarily nested intake structures."""
    if isinstance(value, dict):
        for k, v in value.items():
            yield from iter_scalars(v, str(k))
    elif isinstance(value, (list, tuple)):
        for item in value:
            yield from iter_scalars(item, key)
    elif value is not None:
        yield key, value


_SENTENCE_BREAK = re.compile(r"(?<=[.!?])[\s ]+|\n+")


def sentence_spans(text: str) -> List[Tuple[int, int]]:
    """(start, end) spans of sentences; newlines always break sentences."""
    spans: List[Tuple[int, int]] = []
    start = 0
    for match in _SENTENCE_BREAK.finditer(text):
        if match.start() > start:
            spans.append((start, match.start()))
        start = match.end()
    if start < len(text):
        spans.append((start, len(text)))
    return spans
