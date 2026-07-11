"""
Placeholder fill (finding L15) and party-role correction (finding L1).

Role map ground truth: petitioner/respondent from the profile; the moving
party is the user for RFO sections and declarations, the other party for
response sections; the declarant is always the user. Only the two profile
names participate — exact word-boundary matching, no fuzzy matching or NER.
"""
import re
from typing import Dict, List, Optional, Tuple

from app.services.fact_gate.types import Correction, GateContext, excerpt

_PLACEHOLDER_RE = re.compile(r"\[([A-Z][A-Z'’\s./-]{2,60})\]")
_TITLE_RE = re.compile(r"(?m)^([ \t]*)REQUEST FOR ORDER[ \t]*$")
_RESPONSE_TITLE = "RESPONSIVE DECLARATION TO REQUEST FOR ORDER"
_APPOSITIVE_ROLES = r"(Petitioner|Respondent|Moving\s+Party|Declarant)"


def role_map(ctx: GateContext) -> Dict[str, str]:
    party = (ctx.party_name or "").strip()
    other = (ctx.other_party_name or "").strip()
    petitioner = party if ctx.is_petitioner else other
    respondent = other if ctx.is_petitioner else party
    moving = other if ctx.motion_kind == "response_section" else party
    return {
        "Petitioner": petitioner,
        "Respondent": respondent,
        "Moving Party": moving,
        "Declarant": party,
    }


def _name_regex(*names: str) -> str:
    variants = []
    for name in names:
        parts = name.split()
        if not parts:
            continue
        variants.append(r"\s+".join(re.escape(part) for part in parts))
        if len(parts) > 2:  # allow first+last for middle-name profiles
            variants.append(re.escape(parts[0]) + r"\s+" + re.escape(parts[-1]))
    return "(?:" + "|".join(variants) + ")"


def _matches_person(matched: str, full_name: str) -> bool:
    matched_norm = " ".join(matched.split()).casefold()
    parts = full_name.split()
    if matched_norm == " ".join(parts).casefold():
        return True
    return len(parts) > 2 and matched_norm == f"{parts[0]} {parts[-1]}".casefold()


def _primary_role(name: str, roles: Dict[str, str]) -> Optional[str]:
    if roles["Petitioner"] and _matches_person(name, roles["Petitioner"]):
        return "Petitioner"
    if roles["Respondent"] and _matches_person(name, roles["Respondent"]):
        return "Respondent"
    return None


def _replace_group(match: re.Match, group: int, replacement: str) -> str:
    start = match.start(group) - match.start(0)
    end = match.end(group) - match.start(0)
    whole = match.group(0)
    return whole[:start] + replacement + whole[end:]


def _role_correction(original: str, replacement: str, message: str) -> Correction:
    return Correction(
        type="party_role",
        severity="corrected",
        section="",
        original=excerpt(original),
        replacement=replacement,
        message=message,
    )


def _fix_definitional(
    text: str, roles: Dict[str, str], names_rx: str, corrections: List[Correction]
) -> str:
    patterns = []
    for role, true_name in roles.items():
        if true_name:
            role_rx = role.replace(" ", r"\s+")
            patterns.append((rf"\b{role_rx}(\s+is\s+|\s*:\s*)({names_rx})", role, true_name))
    if roles["Declarant"]:
        patterns.append((rf"\b(Declaration\s+of\s+)({names_rx})", "Declarant", roles["Declarant"]))

    for pattern, role, true_name in patterns:
        def repl(match: re.Match) -> str:
            if _matches_person(match.group(2), true_name):
                return match.group(0)
            fixed = _replace_group(match, 2, true_name)
            corrections.append(_role_correction(
                match.group(0), fixed,
                f"The {role.lower()} in this case is {true_name} — "
                "the draft named the wrong person, so it was corrected.",
            ))
            return fixed
        text = re.sub(pattern, repl, text, flags=re.IGNORECASE)
    return text


def _fix_appositives(
    text: str, roles: Dict[str, str], names_rx: str, corrections: List[Correction]
) -> str:
    patterns = [
        rf"\b({names_rx})\s*\(\s*{_APPOSITIVE_ROLES}\s*\)",
        rf"\b({names_rx}),\s*the\s+{_APPOSITIVE_ROLES}\b",
    ]

    def repl(match: re.Match) -> str:
        name = match.group(1)
        stated = " ".join(match.group(2).split()).title()
        holder = roles.get(stated, "")
        if holder and _matches_person(name, holder):
            return match.group(0)
        true_role = _primary_role(name, roles)
        if true_role is None or true_role == stated:
            return match.group(0)
        fixed = _replace_group(match, 2, true_role)
        corrections.append(_role_correction(
            match.group(0), fixed,
            f"{name} is the {true_role.lower()} in this case — the label was corrected.",
        ))
        return fixed

    for pattern in patterns:
        text = re.sub(pattern, repl, text)
    return text


def _fix_response_title(text: str, ctx: GateContext, corrections: List[Correction]) -> str:
    if ctx.motion_kind != "response_section":
        return text
    new_text, count = _TITLE_RE.subn(rf"\g<1>{_RESPONSE_TITLE}", text)
    if count:
        corrections.append(_role_correction(
            "REQUEST FOR ORDER", _RESPONSE_TITLE,
            "You are responding to a request, not filing one — the title was "
            f"corrected to '{_RESPONSE_TITLE}'.",
        ))
    return new_text


def check_party_roles(text: str, ctx: GateContext) -> Tuple[str, List[Correction]]:
    """Correct party-role statements against the profile role map."""
    corrections: List[Correction] = []
    text = _fix_response_title(text, ctx, corrections)
    if not ((ctx.party_name or "").strip() and (ctx.other_party_name or "").strip()):
        return text, corrections
    roles = role_map(ctx)
    names_rx = _name_regex(ctx.party_name.strip(), ctx.other_party_name.strip())
    text = _fix_definitional(text, roles, names_rx, corrections)
    text = _fix_appositives(text, roles, names_rx, corrections)
    return text, corrections


def _resolve_placeholder(inner: str, roles: Dict[str, str], ctx: GateContext) -> Optional[str]:
    lowered = inner.lower()
    if "name" not in lowered:
        return None
    if "petitioner" in lowered:
        return roles["Petitioner"] or None
    if "respondent" in lowered:
        return roles["Respondent"] or None
    if "declarant" in lowered or "your" in lowered or "full legal" in lowered:
        return (ctx.party_name or "").strip() or None
    return None


def fill_placeholders(text: str, ctx: GateContext) -> Tuple[str, List[Correction]]:
    """Fill bracketed name placeholders from the profile (info severity)."""
    roles = role_map(ctx)
    corrections: List[Correction] = []

    def repl(match: re.Match) -> str:
        name = _resolve_placeholder(match.group(1), roles, ctx)
        if not name:
            return match.group(0)
        corrections.append(Correction(
            type="placeholder_filled",
            severity="info",
            section="",
            original=match.group(0),
            replacement=name,
            message=f"Filled in {name} from your saved case information.",
        ))
        return name

    return _PLACEHOLDER_RE.sub(repl, text), corrections
