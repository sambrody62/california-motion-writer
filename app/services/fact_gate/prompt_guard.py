"""
Prompt-side fact anchor (findings L1/L3/L7 hardening): tells the model the
authoritative party roles, children ages, and fact rules up front so it never
guesses them. The post-generation gate remains the enforcement layer.
"""
from datetime import date
from typing import Any, Dict, List, Optional

from app.services.fact_gate.allowed_facts import _child_age, _parse_full_date

FACT_RULES = (
    "Use ONLY dates and dollar amounts that appear in the user's input; "
    "anything else must be [TO BE COMPLETED]. Output plain text only — "
    "no markdown, no tables, no HTML entities."
)


def _party_lines(context: Dict[str, Any]) -> List[str]:
    party = str(context.get("party_name") or "").strip()
    other = str(context.get("other_party_name") or "").strip()
    if not (party and other):
        return []
    role = "Respondent" if context.get("party_role") == "Respondent" else "Petitioner"
    petitioner, respondent = (party, other) if role == "Petitioner" else (other, party)
    return [
        f"Petitioner is {petitioner}. Respondent is {respondent}. "
        f"You are drafting for the {role}; the declarant is {party}."
    ]


def _child_entry(child: Any, today: date) -> Optional[str]:
    if not isinstance(child, dict):
        return None
    name = str(child.get("name") or "").strip()
    if not name:
        return None
    dob_raw = child.get("date_of_birth") or child.get("dob") or child.get("birthdate")
    dob = _parse_full_date(str(dob_raw).strip()) if dob_raw else None
    age = _child_age(dob, today) if dob else None
    return f"{name} (age {age})" if age is not None else name


def _children_lines(context: Dict[str, Any], today: date) -> List[str]:
    entries = [
        entry
        for entry in (
            _child_entry(child, today) for child in context.get("children_info") or []
        )
        if entry
    ]
    if not entries:
        return []
    return ["The children are: " + ", ".join(entries) + "."]


def build_fact_anchor(context: Dict[str, Any], today: Optional[date] = None) -> str:
    """Authoritative party/children/fact lines to inject into a section prompt."""
    today = today or date.today()
    lines = ["FACTS (authoritative — do not contradict):"]
    lines += _party_lines(context)
    lines += _children_lines(context, today)
    lines.append(FACT_RULES)
    return "\n".join(lines)
