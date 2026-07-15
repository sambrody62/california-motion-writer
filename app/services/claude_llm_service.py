"""
Claude backend for LLM operations (M2).

Routes operations to the right model tier:
- claude-haiku-4-5: chat, intent classification, UPL checks (high volume, low cost)
- claude-opus-4-8: declaration/motion drafting (quality-sensitive legal writing)

The stable system prompt (base prompt + UPL guardrails) is cached via
prompt caching; per-request content goes in the user message.
"""
import base64
import logging
import os
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)

CHAT_MODEL = os.getenv("CLAUDE_CHAT_MODEL", "claude-haiku-4-5")
DRAFTING_MODEL = os.getenv("CLAUDE_DRAFTING_MODEL", "claude-opus-4-8")

OPERATION_MODELS = {
    "chat_response": CHAT_MODEL,
    "intent_classification": CHAT_MODEL,
    "upl_check": CHAT_MODEL,
    "section_rewrite": DRAFTING_MODEL,
    "declaration": DRAFTING_MODEL,
    "best_interests": DRAFTING_MODEL,
    "complete_motion": DRAFTING_MODEL,
    "served_motion_extraction": CHAT_MODEL,
    "evidence_ranking": CHAT_MODEL,
    "conversation_threading": CHAT_MODEL,
    "screenshot_reading": CHAT_MODEL,
    # Verbatim reproduction fidelity matters for citations — use the drafting tier
    "claim_citation": DRAFTING_MODEL,
}

# Mirrors the per-operation output limits used by the Vertex backend
OPERATION_MAX_TOKENS = {
    "chat_response": 1024,
    "intent_classification": 256,
    "upl_check": 512,
    "section_rewrite": 3000,
    "declaration": 4000,
    "best_interests": 3000,
    "complete_motion": 6000,
    "served_motion_extraction": 1024,
    "evidence_ranking": 2000,
    "conversation_threading": 6000,
    "screenshot_reading": 6000,
    "claim_citation": 6000,
}

# PRD compliance section C3: the line between legal information (allowed)
# and legal advice (unauthorized practice of law). Wording reviewed in-session;
# do not edit casually.
UPL_GUARDRAILS = """LEGAL-COMPLIANCE GUARDRAILS (strictly enforced — unauthorized practice of law):
- You provide document preparation and legal information only, never legal advice.
- NEVER recommend a course of action. Do not write "you should", "I recommend", "I advise", or "your best option". When alternatives exist, describe each one neutrally and leave the choice to the user.
- ONLY use facts the user provided. NEVER invent facts, dates, names, events, or allegations. If required information is missing, insert a [TO BE COMPLETED] placeholder instead of guessing.
- NEVER predict what a judge or court will decide, or estimate chances of success.
- When drafting document text, output ONLY the document content — no commentary, no advice, no disclaimers inside the document.
- If asked for advice about what to do, state that this service prepares documents and provides legal information only, and refer the user to their county court self-help center.
- Do NOT cite any statute, rule of court, case, or courthouse address. Do NOT reference other forms or filing fees.
- When drafting document text, output plain text only — no markdown, no tables, no HTML entities."""


class ClaudeLLMService:
    """Thin generation backend; budget checks and prompt building stay in LLMService."""

    def __init__(self, base_system_prompt: str = ""):
        self.base_system_prompt = base_system_prompt
        self._client = None

    @property
    def available(self) -> bool:
        return bool(os.getenv("ANTHROPIC_API_KEY"))

    def _get_client(self):
        if self._client is None:
            from anthropic import AsyncAnthropic

            self._client = AsyncAnthropic()
        return self._client

    def _system_blocks(self) -> list:
        # Stable content only — anything volatile here would invalidate the cache
        text = f"{self.base_system_prompt}\n\n{UPL_GUARDRAILS}".strip()
        return [{"type": "text", "text": text, "cache_control": {"type": "ephemeral"}}]

    async def generate(
        self,
        prompt: str,
        operation: str,
        user_id: Optional[str] = None,
    ) -> Tuple[str, int, str]:
        """Generate text for an operation. Returns (text, total_tokens, model_id)."""
        client = self._get_client()
        model = OPERATION_MODELS.get(operation, DRAFTING_MODEL)
        response = await client.messages.create(
            model=model,
            max_tokens=OPERATION_MAX_TOKENS.get(operation, 3000),
            system=self._system_blocks(),
            messages=[{"role": "user", "content": prompt}],
        )
        text = next((b.text for b in response.content if b.type == "text"), "")
        tokens = response.usage.input_tokens + response.usage.output_tokens
        return text, tokens, model

    async def generate_with_images(
        self,
        prompt: str,
        images: List[Tuple[bytes, str]],
        operation: str,
        user_id: Optional[str] = None,
    ) -> Tuple[str, int, str]:
        """Generate from images + text (e.g. chat screenshots).

        images: list of (raw_bytes, media_type). Returns (text, total_tokens, model_id).
        """
        client = self._get_client()
        model = OPERATION_MODELS.get(operation, CHAT_MODEL)
        content = [
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": media_type,
                    "data": base64.b64encode(raw).decode("ascii"),
                },
            }
            for raw, media_type in images
        ]
        content.append({"type": "text", "text": prompt})
        response = await client.messages.create(
            model=model,
            max_tokens=OPERATION_MAX_TOKENS.get(operation, 3000),
            system=self._system_blocks(),
            messages=[{"role": "user", "content": content}],
        )
        text = next((b.text for b in response.content if b.type == "text"), "")
        tokens = response.usage.input_tokens + response.usage.output_tokens
        return text, tokens, model
