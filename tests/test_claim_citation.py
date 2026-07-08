"""
Tests for claim_citation_service — inline "(Exhibit X)" citations in the
declaration with a zero-drift guardrail. Fallback is ALWAYS the original text.
"""
import asyncio
import pytest
from unittest.mock import AsyncMock

from app.services import claim_citation_service as ccs
from app.services import llm_service as llm_backend

DECLARATION = (
    "Daniel returned the children late on nine occasions since March 2026.\n\n"
    "On May 17, 2026 Sofia missed her school recital because she was returned "
    "at 9:40 p.m.\n\n"
    "I keep a written log of every late return."
)

LETTERED = [
    ("A", {"evidence_type": "email", "source_date": "2026-03-01",
           "description": "Email admitting late return", "tags": ["custody_violation"]}),
    ("B", {"evidence_type": "text", "source_date": "2026-05-17",
           "description": "Text about recital night", "tags": ["custody_violation"]}),
]

CITED_OK = (
    "Daniel returned the children late on nine occasions since March 2026. (Exhibit A)\n\n"
    "On May 17, 2026 Sofia missed her school recital because she was returned "
    "at 9:40 p.m. (Exhibit B)\n\n"
    "I keep a written log of every late return."
)


class TestStripAndValidate:
    def test_strip_citations_removes_all_tokens(self):
        assert ccs.strip_citations(CITED_OK).replace("  ", " ") != CITED_OK
        assert "(Exhibit A)" not in ccs.strip_citations(CITED_OK)
        assert "(Exhibit B)" not in ccs.strip_citations(CITED_OK)

    def test_validate_accepts_faithful_output(self):
        assert ccs.validate_citation_output(DECLARATION, CITED_OK, {"A", "B"}) is True

    def test_validate_rejects_text_drift(self):
        drifted = CITED_OK.replace("nine occasions", "several occasions")
        assert ccs.validate_citation_output(DECLARATION, drifted, {"A", "B"}) is False

    def test_validate_rejects_unknown_exhibit_letter(self):
        assert ccs.validate_citation_output(DECLARATION, CITED_OK, {"A"}) is False

    def test_validate_rejects_dropped_paragraph(self):
        truncated = CITED_OK.split("\n\n")[0]
        assert ccs.validate_citation_output(DECLARATION, truncated, {"A", "B"}) is False

    def test_validate_tolerates_whitespace_differences(self):
        respaced = CITED_OK.replace("\n\n", "\n\n\n")
        assert ccs.validate_citation_output(DECLARATION, respaced, {"A", "B"}) is True


class TestInsertClaimCitations:
    @pytest.mark.asyncio
    async def test_empty_lettered_returns_original(self):
        out = await ccs.insert_claim_citations(DECLARATION, [])
        assert out == DECLARATION

    @pytest.mark.asyncio
    async def test_mock_llm_returns_original(self, monkeypatch):
        monkeypatch.setattr(llm_backend, "USE_MOCK_LLM", True)
        generate = AsyncMock()
        monkeypatch.setattr(llm_backend.llm_service, "_generate", generate)
        out = await ccs.insert_claim_citations(DECLARATION, LETTERED)
        assert out == DECLARATION
        generate.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_llm_exception_returns_original(self, monkeypatch):
        monkeypatch.setattr(llm_backend, "USE_MOCK_LLM", False)
        monkeypatch.setattr(
            llm_backend.llm_service, "_generate",
            AsyncMock(side_effect=RuntimeError("backend down")),
        )
        out = await ccs.insert_claim_citations(DECLARATION, LETTERED)
        assert out == DECLARATION

    @pytest.mark.asyncio
    async def test_timeout_returns_original(self, monkeypatch):
        monkeypatch.setattr(llm_backend, "USE_MOCK_LLM", False)
        monkeypatch.setattr(ccs, "LLM_TIMEOUT_SECONDS", 0.05)

        async def _slow(*a, **k):
            await asyncio.sleep(1)
            return (CITED_OK, 10, "m")

        monkeypatch.setattr(llm_backend.llm_service, "_generate", _slow)
        out = await ccs.insert_claim_citations(DECLARATION, LETTERED)
        assert out == DECLARATION

    @pytest.mark.asyncio
    async def test_valid_llm_output_is_used(self, monkeypatch):
        monkeypatch.setattr(llm_backend, "USE_MOCK_LLM", False)
        monkeypatch.setattr(
            llm_backend.llm_service, "_generate",
            AsyncMock(return_value=(CITED_OK, 100, "claude-sonnet-4-6")),
        )
        out = await ccs.insert_claim_citations(DECLARATION, LETTERED)
        assert out == CITED_OK

    @pytest.mark.asyncio
    async def test_invalid_llm_output_falls_back(self, monkeypatch):
        monkeypatch.setattr(llm_backend, "USE_MOCK_LLM", False)
        drifted = CITED_OK.replace("written log", "detailed diary")
        monkeypatch.setattr(
            llm_backend.llm_service, "_generate",
            AsyncMock(return_value=(drifted, 100, "claude-sonnet-4-6")),
        )
        out = await ccs.insert_claim_citations(DECLARATION, LETTERED)
        assert out == DECLARATION

    @pytest.mark.asyncio
    async def test_no_declaration_content_logged(self, monkeypatch, caplog):
        monkeypatch.setattr(llm_backend, "USE_MOCK_LLM", False)
        monkeypatch.setattr(
            llm_backend.llm_service, "_generate",
            AsyncMock(return_value=(CITED_OK, 100, "m")),
        )
        with caplog.at_level("DEBUG"):
            await ccs.insert_claim_citations(DECLARATION, LETTERED)
        assert "recital" not in caplog.text
        assert "nine occasions" not in caplog.text
