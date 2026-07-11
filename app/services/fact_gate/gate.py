"""
Fact-gate orchestrator. The pass order is load-bearing:

1. markdown strip   — normalizes tokens so **Jacob** can't defeat name regexes
2. authority strip  — citations removed BEFORE the fact passes can see them
3. placeholder fill
4. party roles
5. amounts / dates / ages
6. flag-only scans (UPL, quantifiers)

run_fact_gate NEVER raises: a failing pass is skipped, the text is left
unchanged, and an info Correction records the skip. The gate is idempotent:
run_fact_gate(result.text, ctx).text == result.text.
"""
import logging
from typing import Callable, List, Optional, Tuple

from app.services.fact_gate.allowed_facts import AllowedFacts, build_allowed_facts
from app.services.fact_gate.authority_strip import strip_authority
from app.services.fact_gate.fact_check import check_ages, check_amounts, check_dates
from app.services.fact_gate.flags import scan_flags
from app.services.fact_gate.markdown_strip import strip_markdown
from app.services.fact_gate.party_check import check_party_roles, fill_placeholders
from app.services.fact_gate.types import Correction, GateContext, GateResult

logger = logging.getLogger(__name__)

_Pass = Tuple[str, str, Callable]


def _skipped(name: str, correction_type: str) -> Correction:
    return Correction(
        type=correction_type,
        severity="info",
        section="",
        original="",
        replacement=None,
        message=f"The automated {name} check could not run and was skipped.",
    )


def _build_facts(ctx: GateContext, corrections: List[Correction]) -> Tuple[AllowedFacts, bool]:
    try:
        return build_allowed_facts(ctx), True
    except Exception:
        logger.warning("fact-gate: allowed-facts build failed; fact passes skipped",
                       exc_info=True)
        corrections.append(_skipped("amount, date, and age", "amount"))
        return AllowedFacts(), False


def _passes(ctx: GateContext, facts: AllowedFacts, facts_ok: bool) -> List[_Pass]:
    passes: List[_Pass] = [
        ("formatting", "markdown", strip_markdown),
        ("legal-citation", "authority_removed",
         lambda t: strip_authority(t, facts.address_tokens, ctx)),
        ("placeholder", "placeholder_filled", lambda t: fill_placeholders(t, ctx)),
        ("party-role", "party_role", lambda t: check_party_roles(t, ctx)),
    ]
    if facts_ok:
        passes += [
            ("amount", "amount", lambda t: check_amounts(t, facts)),
            ("date", "date", lambda t: check_dates(t, facts)),
            ("age", "age", lambda t: check_ages(t, facts)),
        ]
    passes.append(("advice-and-quantifier", "upl_flag", lambda t: (t, scan_flags(t))))
    return passes


def run_fact_gate(text: Optional[str], ctx: Optional[GateContext] = None) -> GateResult:
    """Deterministically correct/strip/flag LLM motion text. Never raises."""
    if not isinstance(ctx, GateContext):
        ctx = GateContext()
    current = text if isinstance(text, str) else ""
    corrections: List[Correction] = []
    facts, facts_ok = _build_facts(ctx, corrections)
    for name, correction_type, gate_pass in _passes(ctx, facts, facts_ok):
        try:
            current, new_corrections = gate_pass(current)
        except Exception:
            logger.warning("fact-gate: %s pass failed and was skipped", name, exc_info=True)
            corrections.append(_skipped(name, correction_type))
            continue
        corrections.extend(new_corrections)
    for correction in corrections:
        if not correction.section:
            correction.section = ctx.section_name
    return GateResult(text=current, corrections=corrections)
