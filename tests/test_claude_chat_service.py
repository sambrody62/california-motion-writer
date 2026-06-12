"""
Tests for the Claude chat adapter (M2) — Haiku-backed intent classification
and contextual responses, drop-in compatible with llm_chat_service.
"""
import json
from unittest.mock import AsyncMock

from app.services.claude_chat_service import ClaudeChatService


def _adapter_returning(text: str) -> ClaudeChatService:
    adapter = ClaudeChatService()
    adapter.backend = AsyncMock()
    adapter.backend.generate.return_value = (text, 50, "claude-haiku-4-5")
    return adapter


class TestClassifyIntent:
    async def test_parses_json_classification(self):
        adapter = _adapter_returning(json.dumps({
            "intent": "FILE_MOTION",
            "entities": {"motion_type": "RFO"},
            "confidence": 0.92,
        }))
        intent, entities, confidence = await adapter.classify_intent(
            "my ex violated our custody order"
        )
        assert intent == "FILE_MOTION"
        assert entities == {"motion_type": "RFO"}
        assert confidence == 0.92
        # routed as a classification operation (Haiku tier)
        op = adapter.backend.generate.call_args.args[1]
        assert op == "intent_classification"

    async def test_includes_recent_history_in_prompt(self):
        adapter = _adapter_returning('{"intent": "GET_HELP", "entities": {}, "confidence": 0.8}')
        await adapter.classify_intent(
            "what do I do next?",
            conversation_history=[{"sender": "user", "content": "I got served papers"}],
        )
        prompt = adapter.backend.generate.call_args.args[0]
        assert "I got served papers" in prompt

    async def test_malformed_json_returns_unknown(self):
        adapter = _adapter_returning("I think this is about filing a motion")
        intent, entities, confidence = await adapter.classify_intent("hello")
        assert intent == "UNKNOWN"
        assert entities == {}
        assert confidence == 0.0

    async def test_backend_error_returns_unknown(self):
        adapter = ClaudeChatService()
        adapter.backend = AsyncMock()
        adapter.backend.generate.side_effect = RuntimeError("api down")
        intent, entities, confidence = await adapter.classify_intent("hello")
        assert intent == "UNKNOWN"
        assert confidence == 0.0


class TestGenerateContextualResponse:
    async def test_parses_response_and_quick_replies(self):
        adapter = _adapter_returning(json.dumps({
            "response": "I can help you respond to that motion.",
            "quick_replies": ["Start my response", "What is FL-320?"],
        }))
        text, quick_replies = await adapter.generate_contextual_response(
            session_state="INFORMATION_GATHERING",
            user_message="I got served with an RFO",
            intent="RESPOND_MOTION",
            entities={},
            context={},
        )
        assert text == "I can help you respond to that motion."
        assert quick_replies == ["Start my response", "What is FL-320?"]
        op = adapter.backend.generate.call_args.args[1]
        assert op == "chat_response"

    async def test_plain_text_response_passes_through(self):
        adapter = _adapter_returning("Here is some plain guidance text.")
        text, quick_replies = await adapter.generate_contextual_response(
            session_state="GREETING",
            user_message="hi",
            intent="GET_HELP",
            entities={},
            context={},
        )
        assert text == "Here is some plain guidance text."
        assert quick_replies == []
