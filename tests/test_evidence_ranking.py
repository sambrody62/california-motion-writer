"""
Tests for evidence_ranking_service — LLM relevance ranking of Gmail scan
candidates against the user's intake claims. Metadata only; bodies never
reach the prompt.
"""
import pytest
from unittest.mock import AsyncMock

from app.services import evidence_ranking_service as ers
from app.services import llm_service as llm_backend

CANDIDATES = [
    {"message_id": "msg-1", "from": "daniel@example.com", "date": "2026-03-03",
     "subject": "Late again tonight", "snippet": "Running behind, be there by 9"},
    {"message_id": "msg-2", "from": "daniel@example.com", "date": "2026-01-10",
     "subject": "Fantasy football", "snippet": "Who is on your roster this week"},
]

CLAIMS = "Daniel returned the children late nine times since March 2026."


class TestSanitizeRankings:
    def test_clamps_score_filters_tags_truncates_why(self):
        raw = {
            "rankings": [
                {"message_id": "msg-1", "score": 4.2, "why": "x" * 500,
                 "tags": ["custody_violation", "made_up_tag"]},
                {"message_id": "unknown-id", "score": 0.5, "why": "w", "tags": []},
            ]
        }
        out = ers.sanitize_rankings(raw, {"msg-1", "msg-2"})
        assert set(out.keys()) == {"msg-1"}
        assert out["msg-1"]["score"] == 1.0
        assert len(out["msg-1"]["why"]) <= 200
        assert out["msg-1"]["tags"] == ["custody_violation"]

    def test_non_numeric_score_dropped(self):
        raw = {"rankings": [{"message_id": "msg-1", "score": "high", "why": "w", "tags": []}]}
        assert ers.sanitize_rankings(raw, {"msg-1"}) == {}


class TestBuildClaimsNarrative:
    def test_combines_intake_and_drafts_and_truncates(self):
        intake = {"relief_categories": ["custody"], "emergency_orders": False}
        drafts = [{"changed_circumstances": "Nine late returns " * 400}]
        narrative = ers.build_claims_narrative(intake, drafts)
        assert "custody" in narrative
        assert len(narrative) <= ers.MAX_CLAIMS_CHARS

    def test_empty_inputs_give_empty_narrative(self):
        assert ers.build_claims_narrative({}, []) == ""


class TestRankCandidates:
    @pytest.mark.asyncio
    async def test_mock_llm_returns_unranked_with_notice(self, monkeypatch):
        monkeypatch.setattr(llm_backend, "USE_MOCK_LLM", True)
        generate = AsyncMock()
        monkeypatch.setattr(llm_backend.llm_service, "_generate", generate)

        ranked, notice = await ers.rank_candidates(CANDIDATES, CLAIMS)

        assert notice == ers.NOTICE_UNRANKED
        assert [c["message_id"] for c in ranked] == ["msg-1", "msg-2"]
        assert "relevance_score" not in ranked[0]
        generate.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_empty_claims_skips_llm(self, monkeypatch):
        monkeypatch.setattr(llm_backend, "USE_MOCK_LLM", False)
        generate = AsyncMock()
        monkeypatch.setattr(llm_backend.llm_service, "_generate", generate)

        ranked, notice = await ers.rank_candidates(CANDIDATES, "")

        assert notice == ers.NOTICE_UNRANKED
        generate.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_llm_failure_returns_unranked(self, monkeypatch):
        monkeypatch.setattr(llm_backend, "USE_MOCK_LLM", False)
        monkeypatch.setattr(
            llm_backend.llm_service, "_generate",
            AsyncMock(side_effect=RuntimeError("down")),
        )
        ranked, notice = await ers.rank_candidates(CANDIDATES, CLAIMS)
        assert notice == ers.NOTICE_UNRANKED
        assert len(ranked) == 2

    @pytest.mark.asyncio
    async def test_success_merges_ranking_fields(self, monkeypatch):
        monkeypatch.setattr(llm_backend, "USE_MOCK_LLM", False)
        monkeypatch.setattr(
            llm_backend.llm_service, "_generate",
            AsyncMock(return_value=(
                '{"rankings": [{"message_id": "msg-1", "score": 0.9,'
                ' "why": "Admits being late", "tags": ["custody_violation"]}]}',
                80, "claude-haiku-4-5",
            )),
        )
        ranked, notice = await ers.rank_candidates(CANDIDATES, CLAIMS)

        assert notice is None
        by_id = {c["message_id"]: c for c in ranked}
        assert by_id["msg-1"]["relevance_score"] == 0.9
        assert by_id["msg-1"]["relevance_reason"] == "Admits being late"
        assert by_id["msg-1"]["suggested_tags"] == ["custody_violation"]
        assert "relevance_score" not in by_id["msg-2"]

    @pytest.mark.asyncio
    async def test_prompt_contains_metadata_but_not_bodies(self, monkeypatch):
        monkeypatch.setattr(llm_backend, "USE_MOCK_LLM", False)
        generate = AsyncMock(return_value=('{"rankings": []}', 10, "m"))
        monkeypatch.setattr(llm_backend.llm_service, "_generate", generate)

        candidates = [dict(CANDIDATES[0], body_text="SECRET FULL BODY CONTENT")]
        await ers.rank_candidates(candidates, CLAIMS)

        prompt = generate.await_args.args[0]
        assert "Late again tonight" in prompt          # subject
        assert "Running behind" in prompt              # snippet
        assert "SECRET FULL BODY CONTENT" not in prompt  # body never sent
        assert CLAIMS[:30] in prompt
