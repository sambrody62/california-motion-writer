"""
Enhanced LLM Service for conversational chat with intent recognition and entity extraction
"""
import json
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
import re
from vertexai.generative_models import GenerativeModel, GenerationConfig, SafetySetting, HarmCategory, HarmBlockThreshold
import vertexai

from app.core.config import settings
from app.models.chat import ChatSessionState, ChatSession

logger = logging.getLogger(__name__)

class LLMChatService:
    """Extended LLM service for chat conversations"""

    def __init__(self):
        # Initialize Vertex AI
        vertexai.init(
            project=settings.PROJECT_ID,
            location=settings.VERTEX_AI_LOCATION
        )

        # Initialize conversational model with chat-specific system prompt
        self.chat_model = GenerativeModel(
            model_name=settings.VERTEX_AI_MODEL,
            system_instruction=self._get_chat_system_prompt()
        )

        # Generation config for chat (more conversational)
        self.chat_config = GenerationConfig(
            temperature=0.8,  # Slightly higher for more natural conversation
            top_p=0.95,
            max_output_tokens=1024,  # Shorter for chat responses
        )

        # Generation config for analysis (more precise)
        self.analysis_config = GenerationConfig(
            temperature=0.3,  # Lower for consistent analysis
            top_p=0.9,
            max_output_tokens=512,
        )

        # Safety settings
        self.safety_settings = [
            SafetySetting(
                category=HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                threshold=HarmBlockThreshold.BLOCK_ONLY_HIGH
            ),
            SafetySetting(
                category=HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                threshold=HarmBlockThreshold.BLOCK_ONLY_HIGH
            ),
            SafetySetting(
                category=HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                threshold=HarmBlockThreshold.BLOCK_ONLY_HIGH
            ),
            SafetySetting(
                category=HarmCategory.HARM_CATEGORY_HARASSMENT,
                threshold=HarmBlockThreshold.BLOCK_ONLY_HIGH
            )
        ]

    def _get_chat_system_prompt(self) -> str:
        """System prompt for conversational assistant"""
        return """You are a helpful California family court filing assistant. Your role is to guide users through the process of filing motions and completing court forms through natural conversation.

IMPORTANT GUIDELINES:
1. Be conversational and friendly while maintaining professionalism
2. Ask one question at a time to gather information
3. Provide clear explanations when users are confused
4. Never provide legal advice - only procedural guidance
5. Always clarify ambiguous information
6. Use simple language, avoid legal jargon unless necessary
7. Be empathetic to users going through difficult family situations
8. Guide users toward the appropriate forms based on their situation

CONVERSATION STYLE:
- Start with understanding their situation
- Ask follow-up questions to clarify
- Provide examples when helpful
- Confirm understanding before moving forward
- Summarize what you've learned periodically"""

    async def classify_intent(
        self,
        message: str,
        conversation_history: List[Dict] = None
    ) -> Tuple[str, Dict, float]:
        """
        Use LLM to classify user intent with high accuracy
        Returns: (intent, entities, confidence)
        """
        try:
            # Build context from conversation history
            history_context = ""
            if conversation_history:
                history_context = "Previous conversation:\n"
                for msg in conversation_history[-5:]:  # Last 5 messages for context
                    history_context += f"{msg['sender']}: {msg['content']}\n"

            prompt = f"""Analyze this message and classify the user's intent.

{history_context}

Current message: "{message}"

Classify the PRIMARY intent as one of:
- FILE_MOTION: User wants to file a new motion or request
- RESPOND_MOTION: User needs to respond to papers they received
- MODIFY_ORDER: User wants to change an existing order
- REPORT_VIOLATION: User wants to report a violation of court orders
- GET_HELP: User is asking for help or explanation
- PROVIDE_INFO: User is providing information in response to a question
- CHECK_STATUS: User asking about their progress or what's next
- GREETING: User is greeting or starting conversation
- UNCLEAR: Intent is not clear

Also extract any entities mentioned:
- motion_type: (custody/support/visitation/restraining/other)
- party_type: (petitioner/respondent)
- urgency: (emergency/regular)
- dates: any dates mentioned
- names: any names mentioned
- amounts: any dollar amounts
- children: information about children

Respond in JSON format:
{{
    "intent": "PRIMARY_INTENT",
    "confidence": 0.0-1.0,
    "entities": {{
        "motion_type": "if mentioned",
        "party_type": "if mentioned",
        "urgency": "if mentioned",
        "dates": ["list of dates"],
        "names": ["list of names"],
        "amounts": ["list of amounts"],
        "children": ["ages or info mentioned"]
    }},
    "reasoning": "brief explanation of classification"
}}"""

            response = self.chat_model.generate_content(
                prompt,
                generation_config=self.analysis_config,
                safety_settings=self.safety_settings
            )

            # Parse JSON response
            result = json.loads(response.text)

            intent = result.get("intent", "UNCLEAR")
            confidence = float(result.get("confidence", 0.5))
            entities = result.get("entities", {})

            # Clean up empty entities
            entities = {k: v for k, v in entities.items() if v}

            return intent, entities, confidence

        except json.JSONDecodeError:
            # Don't log the response body — it is derived from case content
            logger.error("Failed to parse LLM response as JSON (%d chars)", len(response.text))
            # Fallback to basic pattern matching
            return self._fallback_intent_classification(message)
        except Exception as e:
            logger.error(f"Intent classification error: {e}")
            return "UNCLEAR", {}, 0.0

    def _fallback_intent_classification(self, message: str) -> Tuple[str, Dict, float]:
        """Fallback pattern-based classification if LLM fails"""
        message_lower = message.lower()
        entities = {}

        # Simple pattern matching
        if any(word in message_lower for word in ["file", "submit", "start", "begin"]):
            intent = "FILE_MOTION"
            confidence = 0.6
        elif any(word in message_lower for word in ["respond", "received", "served", "reply"]):
            intent = "RESPOND_MOTION"
            confidence = 0.6
        elif any(word in message_lower for word in ["modify", "change", "update", "amend"]):
            intent = "MODIFY_ORDER"
            confidence = 0.6
        elif any(word in message_lower for word in ["violate", "violation", "contempt", "not following"]):
            intent = "REPORT_VIOLATION"
            confidence = 0.6
        elif any(word in message_lower for word in ["help", "what", "how", "explain", "confused"]):
            intent = "GET_HELP"
            confidence = 0.5
        elif any(word in message_lower for word in ["hello", "hi", "hey", "good morning"]):
            intent = "GREETING"
            confidence = 0.8
        else:
            intent = "UNCLEAR"
            confidence = 0.3

        # Extract basic entities
        if "custody" in message_lower:
            entities["motion_type"] = "custody"
        elif "support" in message_lower:
            entities["motion_type"] = "support"
        elif "visitation" in message_lower:
            entities["motion_type"] = "visitation"

        if "emergency" in message_lower or "urgent" in message_lower:
            entities["urgency"] = "emergency"

        return intent, entities, confidence

    async def generate_contextual_response(
        self,
        session_state: ChatSessionState,
        user_message: str,
        intent: str,
        entities: Dict,
        context: Dict
    ) -> Tuple[str, List[str]]:
        """
        Generate a contextual response based on conversation state
        Returns: (response_text, quick_replies)
        """
        try:
            # Build context prompt
            context_prompt = self._build_context_prompt(session_state, context)

            prompt = f"""Given the conversation context, generate an appropriate response.

Context:
{context_prompt}

Current State: {session_state.value}
User Message: "{user_message}"
Detected Intent: {intent}
Extracted Entities: {json.dumps(entities)}

Generate a helpful response that:
1. Acknowledges what the user said
2. Asks the next relevant question OR provides requested information
3. Guides them toward their goal
4. Is conversational and empathetic

Also suggest 2-4 quick reply options that would be most helpful for the user to choose from.

Respond in JSON format:
{{
    "response": "Your response message here",
    "quick_replies": ["Option 1", "Option 2", "Option 3"],
    "next_state": "suggested next conversation state"
}}"""

            response = self.chat_model.generate_content(
                prompt,
                generation_config=self.chat_config,
                safety_settings=self.safety_settings
            )

            # Parse response
            result = json.loads(response.text)

            response_text = result.get("response", "I understand. Let me help you with that.")
            quick_replies = result.get("quick_replies", [])

            return response_text, quick_replies

        except json.JSONDecodeError:
            # If JSON parsing fails, extract text directly
            response_text = response.text if response else "I understand. Could you tell me more about your situation?"
            quick_replies = self._get_default_quick_replies(session_state)
            return response_text, quick_replies
        except Exception as e:
            logger.error(f"Response generation error: {e}")
            return "I understand you need help. Could you tell me more about what you're trying to do?", []

    def _build_context_prompt(self, state: ChatSessionState, context: Dict) -> str:
        """Build context description for the LLM"""
        context_parts = []

        # Add state context
        state_descriptions = {
            ChatSessionState.GREETING: "User just started the conversation",
            ChatSessionState.MOTION_SELECTION: "User is selecting what type of motion to file",
            ChatSessionState.INFORMATION_GATHERING: "Gathering information for the motion",
            ChatSessionState.REVIEW: "Reviewing collected information",
            ChatSessionState.PDF_GENERATION: "Ready to generate documents"
        }
        context_parts.append(f"Conversation Stage: {state_descriptions.get(state, 'In progress')}")

        # Add collected information
        if context:
            context_parts.append("Information collected so far:")
            for key, value in context.items():
                if value:
                    context_parts.append(f"- {key}: {value}")

        return "\n".join(context_parts)

    def _get_default_quick_replies(self, state: ChatSessionState) -> List[str]:
        """Get default quick replies for a given state"""
        defaults = {
            ChatSessionState.GREETING: [
                "File a new motion",
                "Respond to papers",
                "Get help",
                "Check my progress"
            ],
            ChatSessionState.MOTION_SELECTION: [
                "Custody modification",
                "Support change",
                "Report a violation",
                "Something else"
            ],
            ChatSessionState.INFORMATION_GATHERING: [
                "Yes",
                "No",
                "I'm not sure",
                "Skip this question"
            ]
        }
        return defaults.get(state, ["Continue", "Go back", "Get help"])

    async def extract_form_fields(
        self,
        conversation_messages: List[Dict],
        target_form: str
    ) -> Dict[str, Any]:
        """
        Extract form field values from conversation history
        """
        try:
            # Build conversation text
            conversation_text = "\n".join([
                f"{msg['sender']}: {msg['content']}"
                for msg in conversation_messages
            ])

            prompt = f"""Extract information from this conversation that maps to form {target_form} fields.

Conversation:
{conversation_text}

Extract the following fields if mentioned:
- Party names (petitioner/respondent)
- Case number
- County
- Children (names, ages, birthdates)
- Current custody arrangement
- Requested changes
- Support amounts (current and requested)
- Dates (filing date, hearing date, incident dates)
- Addresses
- Phone numbers
- Email addresses
- Specific requests being made

Return extracted data in JSON format with field names as keys."""

            response = self.chat_model.generate_content(
                prompt,
                generation_config=self.analysis_config,
                safety_settings=self.safety_settings
            )

            # Parse and return extracted fields
            extracted = json.loads(response.text)
            return extracted

        except Exception as e:
            logger.error(f"Field extraction error: {e}")
            return {}

    async def summarize_conversation(
        self,
        messages: List[Dict],
        max_length: int = 500
    ) -> str:
        """
        Summarize a long conversation for context preservation
        """
        try:
            conversation_text = "\n".join([
                f"{msg['sender']}: {msg['content'][:200]}"  # Limit each message
                for msg in messages
            ])

            prompt = f"""Summarize this conversation in {max_length} words or less.

Focus on:
1. What the user is trying to accomplish
2. Key information already collected
3. Any issues or concerns raised
4. Current status/next steps

Conversation:
{conversation_text}

Provide a concise summary:"""

            response = self.chat_model.generate_content(
                prompt,
                generation_config=self.analysis_config,
                safety_settings=self.safety_settings
            )

            return response.text[:max_length] if response.text else ""

        except Exception as e:
            logger.error(f"Summarization error: {e}")
            return "Conversation in progress about filing court motions."

    async def validate_information(
        self,
        field_name: str,
        value: str,
        field_type: str = "text"
    ) -> Tuple[bool, Optional[str], Any]:
        """
        Validate extracted information for accuracy and completeness
        Returns: (is_valid, error_message, cleaned_value)
        """
        try:
            prompt = f"""Validate this form field value:

Field: {field_name}
Value: "{value}"
Expected Type: {field_type}

Check if the value is:
1. Valid for this field type
2. Complete and not ambiguous
3. Properly formatted

Respond in JSON:
{{
    "valid": true/false,
    "error": "error message if invalid",
    "cleaned_value": "properly formatted value",
    "suggestions": ["list of suggestions if invalid"]
}}"""

            response = self.chat_model.generate_content(
                prompt,
                generation_config=self.analysis_config,
                safety_settings=self.safety_settings
            )

            result = json.loads(response.text)

            return (
                result.get("valid", False),
                result.get("error"),
                result.get("cleaned_value", value)
            )

        except Exception as e:
            logger.error(f"Validation error: {e}")
            # Basic validation fallback
            return True, None, value

    async def generate_clarification_question(
        self,
        field_name: str,
        current_value: str,
        issue: str
    ) -> str:
        """
        Generate a clarification question for ambiguous or incomplete information
        """
        try:
            prompt = f"""Generate a friendly clarification question.

Field needed: {field_name}
Current value provided: "{current_value}"
Issue: {issue}

Generate a clear, friendly question to get the correct information.
Don't use legal jargon. Be conversational.

Question:"""

            response = self.chat_model.generate_content(
                prompt,
                generation_config=self.chat_config,
                safety_settings=self.safety_settings
            )

            return response.text if response.text else f"Could you clarify the {field_name}?"

        except Exception as e:
            logger.error(f"Clarification generation error: {e}")
            return f"I need to clarify the {field_name}. Could you provide more details?"

# Singleton instance
llm_chat_service = LLMChatService()