"""
Tests for the Claude LLM backend (M2) and its routing in LLMService.
"""
import os
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.claude_llm_service import (
    CHAT_MODEL,
    DRAFTING_MODEL,
    OPERATION_MAX_TOKENS,
    OPERATION_MODELS,
    UPL_GUARDRAILS,
    ClaudeLLMService,
)


def _mock_response(text="Generated text", input_tokens=100, output_tokens=50):
    block = MagicMock()
    block.type = "text"
    block.text = text
    response = MagicMock()
    response.content = [block]
    response.usage.input_tokens = input_tokens
    response.usage.output_tokens = output_tokens
    return response


def _service_with_mock_client(text="Generated text"):
    service = ClaudeLLMService(base_system_prompt="Base legal writing prompt")
    client = AsyncMock()
    client.messages.create.return_value = _mock_response(text)
    service._client = client
    return service, client


class TestOperationRouting:
    def test_drafting_operations_use_drafting_tier(self):
        for op in ("section_rewrite", "declaration", "best_interests", "complete_motion"):
            assert OPERATION_MODELS[op] == DRAFTING_MODEL

    def test_chat_operations_use_haiku(self):
        for op in ("chat_response", "intent_classification", "upl_check"):
            assert OPERATION_MODELS[op] == CHAT_MODEL

    def test_evidence_finder_operations_registered(self):
        assert OPERATION_MODELS["evidence_ranking"] == CHAT_MODEL
        assert OPERATION_MODELS["conversation_threading"] == CHAT_MODEL
        assert OPERATION_MODELS["claim_citation"] == DRAFTING_MODEL
        assert OPERATION_MAX_TOKENS["evidence_ranking"] == 2000
        assert OPERATION_MAX_TOKENS["conversation_threading"] == 6000
        assert OPERATION_MAX_TOKENS["claim_citation"] == 6000

    def test_default_model_ids(self):
        assert DRAFTING_MODEL == "claude-opus-4-8"
        assert CHAT_MODEL == "claude-haiku-4-5"

    def test_max_tokens_match_existing_operation_limits(self):
        assert OPERATION_MAX_TOKENS["chat_response"] == 1024
        assert OPERATION_MAX_TOKENS["section_rewrite"] == 3000
        assert OPERATION_MAX_TOKENS["declaration"] == 4000
        assert OPERATION_MAX_TOKENS["complete_motion"] == 6000


class TestGenerate:
    async def test_returns_text_tokens_and_model(self):
        service, client = _service_with_mock_client()
        text, tokens, model = await service.generate("Rewrite this", "declaration")
        assert text == "Generated text"
        assert tokens == 150  # input + output from usage
        assert model == DRAFTING_MODEL
        kwargs = client.messages.create.call_args.kwargs
        assert kwargs["model"] == DRAFTING_MODEL
        assert kwargs["max_tokens"] == 4000
        assert kwargs["messages"] == [{"role": "user", "content": "Rewrite this"}]

    async def test_chat_operation_uses_haiku_and_short_limit(self):
        service, client = _service_with_mock_client()
        _, _, model = await service.generate("Hi", "chat_response")
        assert model == CHAT_MODEL
        kwargs = client.messages.create.call_args.kwargs
        assert kwargs["model"] == CHAT_MODEL
        assert kwargs["max_tokens"] == 1024

    async def test_unknown_operation_defaults_to_drafting_model(self):
        service, client = _service_with_mock_client()
        _, _, model = await service.generate("text", "unknown_op")
        assert model == DRAFTING_MODEL

    async def test_system_prompt_has_guardrails_and_cache_control(self):
        service, client = _service_with_mock_client()
        await service.generate("prompt", "declaration")
        system = client.messages.create.call_args.kwargs["system"]
        assert isinstance(system, list)
        first = system[0]
        assert "Base legal writing prompt" in first["text"]
        assert UPL_GUARDRAILS in first["text"]
        assert first["cache_control"] == {"type": "ephemeral"}


class TestAvailability:
    def test_unavailable_without_api_key(self, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        assert ClaudeLLMService().available is False

    def test_available_with_api_key(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        assert ClaudeLLMService().available is True


class TestUPLGuardrailContent:
    """The guardrail text is a legal-compliance requirement (PRD section C3)."""

    def test_forbids_recommending_a_course_of_action(self):
        lowered = UPL_GUARDRAILS.lower()
        assert "never recommend" in lowered
        assert "you should" in lowered  # named as a forbidden phrase

    def test_forbids_inventing_facts(self):
        lowered = UPL_GUARDRAILS.lower()
        assert "never invent" in lowered or "never fabricate" in lowered

    def test_forbids_outcome_prediction(self):
        assert "predict" in UPL_GUARDRAILS.lower()

    def test_refers_to_self_help_center(self):
        assert "self-help" in UPL_GUARDRAILS.lower()


class TestLLMServiceClaudeRouting:
    async def test_generate_helper_routes_to_claude_backend(self):
        from app.services.llm_service import LLMService

        service = LLMService()  # mock mode under tests
        backend = AsyncMock()
        backend.generate.return_value = ("claude text", 42, DRAFTING_MODEL)
        service.claude_backend = backend

        text, tokens, model = await service._generate("p", "declaration", None)
        assert text == "claude text"
        assert tokens == 42
        assert model == DRAFTING_MODEL
        backend.generate.assert_awaited_once_with("p", "declaration", None)


class TestValidateOutputUPLFlags:
    def _filler(self):
        return " ".join(["The parties share custody of the children."] * 12)

    def test_flags_advice_phrases(self):
        from app.services.llm_service import llm_service

        result = llm_service.validate_output(
            "You should file an ex parte application immediately. " + self._filler()
        )
        assert result["valid"] is False
        assert result["upl_flags"]
        assert any("you should" in f.lower() for f in result["upl_flags"])

    def test_flags_recommendations(self):
        from app.services.llm_service import llm_service

        result = llm_service.validate_output(
            "I recommend requesting sole legal custody. " + self._filler()
        )
        assert result["valid"] is False
        assert result["upl_flags"]

    def test_clean_document_has_no_upl_flags(self):
        from app.services.llm_service import llm_service

        result = llm_service.validate_output(
            "1. I, John Smith, declare as follows. " + self._filler()
        )
        assert result["upl_flags"] == []


class TestGenerateWithImages:
    def test_screenshot_reading_operation_registered(self):
        assert OPERATION_MODELS["screenshot_reading"] == CHAT_MODEL
        assert OPERATION_MAX_TOKENS["screenshot_reading"] == 6000

    @pytest.mark.asyncio
    async def test_builds_image_blocks_then_text_block(self):
        import base64

        service, client = _service_with_mock_client('{"transcript": "ok"}')
        images = [(b"png-bytes", "image/png"), (b"jpg-bytes", "image/jpeg")]

        text, tokens, model = await service.generate_with_images(
            "Read these screenshots", images, "screenshot_reading"
        )

        assert text == '{"transcript": "ok"}'
        assert tokens == 150
        call = client.messages.create.call_args
        assert call.kwargs["model"] == CHAT_MODEL
        assert call.kwargs["max_tokens"] == 6000
        assert call.kwargs["system"] == service._system_blocks()

        content = call.kwargs["messages"][0]["content"]
        assert len(content) == 3
        assert content[0]["type"] == "image"
        assert content[0]["source"]["type"] == "base64"
        assert content[0]["source"]["media_type"] == "image/png"
        assert base64.b64decode(content[0]["source"]["data"]) == b"png-bytes"
        assert content[1]["source"]["media_type"] == "image/jpeg"
        assert content[2] == {"type": "text", "text": "Read these screenshots"}
