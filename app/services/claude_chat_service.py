"""
Claude chat adapter (M2): Haiku-backed intent classification and contextual
responses, drop-in compatible with llm_chat_service's interface so
ChatService can use either backend.
"""
import json
import logging
from typing import Dict, List, Optional, Tuple

from app.services.claude_llm_service import ClaudeLLMService

logger = logging.getLogger(__name__)

KNOWN_INTENTS = ["FILE_MOTION", "RESPOND_MOTION", "GET_HELP", "UNKNOWN"]

CLASSIFY_PROMPT = """Classify the user's intent for a California family court self-help service.

{history}User message: {message}

Intents: FILE_MOTION (wants to file/modify/enforce an order, including violations),
RESPOND_MOTION (was served papers and needs to respond), GET_HELP (general questions,
confusion), UNKNOWN (none of the above).

Respond with ONLY a JSON object: {{"intent": "<one of the intents>",
"entities": {{<any names, dates, amounts, motion types mentioned>}},
"confidence": <0.0-1.0>}}"""

RESPONSE_PROMPT = """You are the guided assistant for a California family court document-preparation service.
Conversation state: {session_state}
Detected intent: {intent}
Known context: {context}

User message: {user_message}

Reply with ONLY a JSON object: {{"response": "<your reply — plain language, warm,
informational only, never legal advice, never a recommendation between legal options>",
"quick_replies": ["<up to 3 short next-step buttons>"]}}"""


class ClaudeChatService:
    def __init__(self):
        self.backend = ClaudeLLMService()

    @property
    def available(self) -> bool:
        return self.backend.available

    async def classify_intent(
        self,
        message: str,
        conversation_history: Optional[List[Dict]] = None,
    ) -> Tuple[str, Dict, float]:
        """Returns (intent, entities, confidence); UNKNOWN on any failure."""
        history = ""
        if conversation_history:
            lines = [
                f"{m['sender']}: {m['content']}" for m in conversation_history[-5:]
            ]
            history = "Previous conversation:\n" + "\n".join(lines) + "\n\n"
        prompt = CLASSIFY_PROMPT.format(history=history, message=message)
        try:
            text, _, _ = await self.backend.generate(prompt, "intent_classification")
            data = json.loads(text)
            intent = data.get("intent", "UNKNOWN")
            if intent not in KNOWN_INTENTS:
                intent = "UNKNOWN"
            return intent, data.get("entities", {}) or {}, float(data.get("confidence", 0.0))
        except Exception as e:
            logger.warning(f"Claude intent classification failed: {e}")
            return "UNKNOWN", {}, 0.0

    async def generate_contextual_response(
        self,
        session_state,
        user_message: str,
        intent: str,
        entities: Dict,
        context: Dict,
    ) -> Tuple[str, List[str]]:
        """Returns (response_text, quick_replies); plain text passes through."""
        prompt = RESPONSE_PROMPT.format(
            session_state=session_state,
            intent=intent,
            context=json.dumps(context or {}, default=str),
            user_message=user_message,
        )
        text, _, _ = await self.backend.generate(prompt, "chat_response")
        try:
            data = json.loads(text)
            return data.get("response", text), data.get("quick_replies", []) or []
        except (json.JSONDecodeError, TypeError):
            return text, []


claude_chat_service = ClaudeChatService()
