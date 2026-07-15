"""
Unit tests for the LLM semantic refute-pass (app/services/semantic_check_service).

The checker is flag-only and fail-open: malformed output, backend errors, and
timeouts must all yield [] so motion processing is never blocked.
"""
import asyncio
import json
from unittest.mock import AsyncMock

import pytest

from app.services import llm_service as llm_module
from app.services import semantic_check_service

pytestmark = pytest.mark.asyncio

INTAKE = {
    "violationDescription": "Respondent denied the visit.",
    "violationDates": ["2026-06-20"],
}
CONTEXT = {"party_name": "Rosa Martinez", "county": "San Diego"}
TEXT = "Respondent has denied visits on at least twelve occasions."


def _findings_json(findings) -> str:
    return json.dumps({"findings": findings})


def _real_backend(monkeypatch, raw_response: str) -> AsyncMock:
    """Point the singleton at a fake Claude backend with mock mode off."""
    monkeypatch.setattr(llm_module, "USE_MOCK_LLM", False)
    backend = AsyncMock()
    backend.generate.return_value = (raw_response, 100, "claude-opus-4-8")
    monkeypatch.setattr(llm_module.llm_service, "claude_backend", backend)
    return backend


async def test_maps_findings_to_needs_review_corrections(monkeypatch):
    backend = _real_backend(
        monkeypatch,
        _findings_json(
            [
                {
                    "claim": "at least twelve occasions",
                    "reason": "The intake data does not say how many visits were denied.",
                }
            ]
        ),
    )

    corrections = await semantic_check_service.check_text(TEXT, INTAKE, CONTEXT)

    assert corrections == [
        {
            "type": "semantic_flag",
            "severity": "needs_review",
            "section": "reviewer",
            "original": "at least twelve occasions",
            "replacement": None,
            "message": (
                "Our automated reviewer flagged: The intake data does not say "
                "how many visits were denied. — verify "
                '"at least twelve occasions" against your records before filing.'
            ),
        }
    ]
    backend.generate.assert_awaited_once()
    prompt, operation = backend.generate.await_args.args
    assert operation == "semantic_check"
    assert TEXT in prompt
    assert "REFUTE" in prompt
    # Intake and profile context are presented as key: value scalar lines
    assert "party_name: Rosa Martinez" in prompt
    assert "violationDescription: Respondent denied the visit." in prompt
    assert "violationDates: 2026-06-20" in prompt


async def test_long_claims_truncated_to_120_chars(monkeypatch):
    _real_backend(
        monkeypatch, _findings_json([{"claim": "x" * 200, "reason": "Not supported."}])
    )
    corrections = await semantic_check_service.check_text(TEXT, INTAKE, CONTEXT)
    assert len(corrections) == 1
    assert corrections[0]["original"] == "x" * 120


async def test_findings_capped_at_ten(monkeypatch):
    findings = [{"claim": f"claim {i}", "reason": f"reason {i}"} for i in range(15)]
    _real_backend(monkeypatch, _findings_json(findings))
    corrections = await semantic_check_service.check_text(TEXT, INTAKE, CONTEXT)
    assert len(corrections) == 10


async def test_malformed_json_returns_empty(monkeypatch):
    _real_backend(monkeypatch, "The document looks mostly fine to me.")
    assert await semantic_check_service.check_text(TEXT, INTAKE, CONTEXT) == []


async def test_invalid_finding_shapes_are_skipped(monkeypatch):
    _real_backend(
        monkeypatch,
        _findings_json(
            [
                "not a dict",
                {"claim": 42, "reason": "wrongly typed claim"},
                {"claim": "   ", "reason": "blank claim"},
                {"claim": "missing reason"},
                {"claim": "real claim", "reason": "real reason"},
            ]
        ),
    )
    corrections = await semantic_check_service.check_text(TEXT, INTAKE, CONTEXT)
    assert [c["original"] for c in corrections] == ["real claim"]


async def test_findings_not_a_list_returns_empty(monkeypatch):
    _real_backend(monkeypatch, json.dumps({"findings": {"claim": "x", "reason": "y"}}))
    assert await semantic_check_service.check_text(TEXT, INTAKE, CONTEXT) == []


async def test_generate_error_fails_open(monkeypatch):
    backend = _real_backend(monkeypatch, "unused")
    backend.generate.side_effect = RuntimeError("api down")
    assert await semantic_check_service.check_text(TEXT, INTAKE, CONTEXT) == []


async def test_timeout_fails_open(monkeypatch):
    backend = _real_backend(monkeypatch, "unused")

    async def slow_generate(prompt, operation, user_id=None):
        await asyncio.sleep(5)
        return ("{}", 0, "claude-opus-4-8")

    backend.generate = slow_generate
    monkeypatch.setattr(semantic_check_service, "TIMEOUT_SECONDS", 0.01)
    assert await semantic_check_service.check_text(TEXT, INTAKE, CONTEXT) == []


async def test_mock_llm_mode_is_honest_noop(monkeypatch):
    monkeypatch.setattr(llm_module, "USE_MOCK_LLM", True)
    backend = AsyncMock()
    monkeypatch.setattr(llm_module.llm_service, "claude_backend", backend)
    assert await semantic_check_service.check_text(TEXT, INTAKE, CONTEXT) == []
    backend.generate.assert_not_awaited()


async def test_no_claude_backend_returns_empty(monkeypatch):
    monkeypatch.setattr(llm_module, "USE_MOCK_LLM", False)
    monkeypatch.setattr(llm_module.llm_service, "claude_backend", None)
    assert await semantic_check_service.check_text(TEXT, INTAKE, CONTEXT) == []
