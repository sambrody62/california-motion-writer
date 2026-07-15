"""
LLM semantic refute-pass over generated motion text.

Complements the deterministic fact gate (app/services/fact_gate): the gate's
regexes catch mechanical fabrications (names, dates, amounts, authorities);
this pass asks the drafting-tier model to refute semantic embellishments the
regexes cannot see. Flag-only — it never edits text — and fail-open: any
error or timeout returns [] so motion processing is never blocked.
"""
import asyncio
import logging
from typing import Any, Dict, List

from app.services.fact_gate.types import iter_scalars
from app.services.llm_json import parse_llm_json

logger = logging.getLogger(__name__)

TIMEOUT_SECONDS = 20.0
MAX_FINDINGS = 10
CLAIM_LIMIT = 120

_INSTRUCTIONS = (
    "You are a skeptical reviewer. Try to REFUTE this document: list every "
    "factual claim (name, date, amount, event, frequency/quantity) that is "
    "NOT supported by the intake data above, and any sentence that recommends "
    "a course of action (legal advice). Do NOT rewrite anything. Return "
    'STRICT JSON: {"findings": [{"claim": "<verbatim excerpt ≤120 chars>", '
    '"reason": "<one plain-English sentence>"}]} — empty findings array if '
    "nothing to flag."
)


async def check_text(
    generated_text: str,
    intake_values: Dict[str, Any],
    context: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """Adversarial review of generated text; correction dicts, [] on any failure."""
    try:
        return await asyncio.wait_for(
            _run_check(generated_text, intake_values, context),
            timeout=TIMEOUT_SECONDS,
        )
    except Exception as exc:  # fail-open: the checker must never block processing
        logger.warning("Semantic check skipped: %s", exc)
        return []


async def _run_check(
    generated_text: str,
    intake_values: Dict[str, Any],
    context: Dict[str, Any],
) -> List[Dict[str, Any]]:
    # Resolved at call time, not import time: test_e2e_regressions reloads
    # app.services.llm_service mid-suite, so a bound import could go stale.
    from app.services import llm_service as llm

    if llm.USE_MOCK_LLM or llm.llm_service.claude_backend is None:
        return []  # honest no-op — never fabricate review results
    prompt = _build_prompt(generated_text, intake_values, context)
    raw, _tokens, _model = await llm.llm_service.claude_backend.generate(
        prompt, "semantic_check"
    )
    return _to_corrections(parse_llm_json(raw))


def _build_prompt(
    generated_text: str,
    intake_values: Dict[str, Any],
    context: Dict[str, Any],
) -> str:
    lines = [
        f"{key}: {value}"
        for source in (context or {}, intake_values or {})
        for key, value in iter_scalars(source)
        if key
    ]
    facts = "\n".join(lines) or "(none provided)"
    return (
        "INTAKE DATA (the only permitted source of facts):\n"
        f"{facts}\n\n"
        "GENERATED DOCUMENT:\n"
        f"{generated_text}\n\n"
        f"{_INSTRUCTIONS}"
    )


def _to_corrections(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Validate the findings payload and map it to fact-check correction dicts."""
    findings = data.get("findings")
    if not isinstance(findings, list):
        return []
    corrections: List[Dict[str, Any]] = []
    for finding in findings[:MAX_FINDINGS]:
        if not isinstance(finding, dict):
            continue
        claim, reason = finding.get("claim"), finding.get("reason")
        if not isinstance(claim, str) or not isinstance(reason, str):
            continue
        claim, reason = claim.strip()[:CLAIM_LIMIT], reason.strip()
        if not claim or not reason:
            continue
        corrections.append(
            {
                "type": "semantic_flag",
                "severity": "needs_review",
                "section": "reviewer",
                "original": claim,
                "replacement": None,
                "message": (
                    f"Our automated reviewer flagged: {reason} — "
                    f'verify "{claim}" against your records before filing.'
                ),
            }
        )
    return corrections
