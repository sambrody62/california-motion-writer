"""
Chat service for managing conversations and message processing
"""
import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc
from sqlalchemy.orm import selectinload
import re

from app.models.chat import (
    ChatSession, ChatMessage, ChatSessionStatus, ChatSessionState,
    MessageSender, ChatIntent, ConversationTemplate
)
from app.models.user import User, Profile
from app.models.motion import Motion, MotionType
import os
# Choose LLM service based on environment variables
if os.getenv("USE_CLAUDE", "false").lower() == "true":
    # llm_service routes generation to the Claude backend when USE_CLAUDE is set
    from app.services.llm_service import LLMService
elif os.getenv("USE_OPENAI", "false").lower() == "true":
    from app.services.openai_llm_service import OpenAILLMService as LLMService
elif os.getenv("USE_GCP", "false").lower() == "true" and os.getenv("USE_MOCK_LLM", "false").lower() == "false":
    from app.services.vertex_llm_service import VertexLLMService as LLMService
else:
    from app.services.llm_service import LLMService
from app.services.violation_service import ViolationFilingService

logger = logging.getLogger(__name__)

class ChatService:
    """Handle chat sessions, messages, and conversation flow"""

    def __init__(self):
        self.llm_service = LLMService()
        self.violation_service = ViolationFilingService()

        # Try to import enhanced LLM chat service if available
        if os.getenv("USE_CLAUDE", "false").lower() == "true":
            from app.services.claude_chat_service import claude_chat_service
            self.llm_chat_service = claude_chat_service
            self.use_llm = claude_chat_service.available
            logger.info(
                "Using Claude chat service"
                if self.use_llm
                else "USE_CLAUDE set but ANTHROPIC_API_KEY missing — pattern-based fallback"
            )
        else:
            try:
                from app.services.llm_chat_service import llm_chat_service
                self.llm_chat_service = llm_chat_service
                self.use_llm = True
                logger.info("Using enhanced LLM chat service")
            except ImportError:
                self.llm_chat_service = None
                self.use_llm = False
                logger.info("Using pattern-based chat service")

        # Import memory and template services
        try:
            from app.services.conversation_memory_service import memory_service
            from app.services.conversation_templates import conversation_templates
            from app.services.question_graph_service import question_graph
            from app.services.form_field_mapper import form_mapper
            self.memory_service = memory_service
            self.templates = conversation_templates
            self.question_graph = question_graph
            self.form_mapper = form_mapper
            logger.info("Memory and template services loaded")
        except ImportError as e:
            logger.warning(f"Could not load additional services: {e}")

        # Intent patterns for basic recognition
        self.intent_patterns = {
            "FILE_MOTION": [
                r"file.*motion", r"request.*order", r"want.*custody", r"need.*support",
                r"modify.*order", r"change.*custody", r"emergency.*order", r"violation"
            ],
            "RESPOND_MOTION": [
                r"respond", r"response", r"received.*papers", r"served.*with",
                r"got.*court.*papers", r"reply.*to"
            ],
            "GET_HELP": [
                r"help", r"what.*can.*do", r"how.*does.*work", r"explain",
                r"don't.*understand", r"confused"
            ],
            "CHECK_STATUS": [
                r"status", r"where.*am.*i", r"progress", r"what.*next"
            ]
        }

        # Quick replies for different states
        self.quick_replies = {
            ChatSessionState.GREETING: [
                "I need to file a motion",
                "I need to respond to papers",
                "I have a question",
                "Check my previous work"
            ],
            ChatSessionState.MOTION_SELECTION: [
                "Request for custody change",
                "Request for support modification",
                "Report a violation",
                "Emergency order",
                "Not sure what I need"
            ]
        }

    async def create_session(
        self,
        db: AsyncSession,
        user_id: str,
        initial_message: Optional[str] = None
    ) -> ChatSession:
        """Create a new chat session"""
        try:
            import uuid

            # Log the user_id to debug
            logger.info(f"Creating session for user_id: {user_id}, type: {type(user_id)}")

            # For SQLite, use string comparison
            # Check for existing active session
            stmt = select(ChatSession).where(
                and_(
                    ChatSession.user_id == user_id,  # SQLite stores UUIDs as strings
                    ChatSession.status == ChatSessionStatus.ACTIVE  # SQLEnum handles the comparison
                )
            ).order_by(desc(ChatSession.started_at)).limit(1)  # Ensure we only get one

            result = await db.execute(stmt)
            existing_session = result.scalar_one_or_none()

            # Resume or create new
            if existing_session and (
                datetime.utcnow() - existing_session.last_message_at < timedelta(hours=1)
            ):
                # Resume existing session if recent
                return existing_session

            # Create new session
            session = ChatSession(
                user_id=user_id,  # SQLite stores UUIDs as strings
                status=ChatSessionStatus.ACTIVE,
                current_state=ChatSessionState.GREETING,
                context={}
            )
            db.add(session)
            await db.commit()

            # Add system greeting
            await self.add_message(
                db,
                session.id,
                self._get_greeting_message(initial_message),
                MessageSender.ASSISTANT,
                quick_replies=self.quick_replies[ChatSessionState.GREETING]
            )

            return session

        except Exception as e:
            logger.error(f"Error creating chat session: {e}")
            raise

    async def add_message(
        self,
        db: AsyncSession,
        session_id: str,
        content: str,
        sender: MessageSender,
        entities: Optional[Dict] = None,
        quick_replies: Optional[List[str]] = None,
        attachments: Optional[List[Dict]] = None
    ) -> ChatMessage:
        """Add a message to the chat session"""
        import uuid
        # Convert string session_id to UUID object
        if isinstance(session_id, str):
            session_uuid = uuid.UUID(session_id)
        else:
            session_uuid = session_id

        message = ChatMessage(
            session_id=session_uuid,
            content=content,
            sender=sender,
            entities=entities or {},
            quick_replies=quick_replies or [],
            attachments=attachments or []
        )
        db.add(message)

        # Update session last message time
        stmt = select(ChatSession).where(ChatSession.id == session_uuid)
        result = await db.execute(stmt)
        session = result.scalar_one()
        session.last_message_at = datetime.utcnow()

        await db.commit()
        return message

    async def process_user_message(
        self,
        db: AsyncSession,
        session_id: str,
        user_message: str,
        user_id: str
    ) -> Dict[str, Any]:
        """Process incoming user message and generate response"""
        try:
            import uuid
            # Convert string session_id to UUID for query
            session_uuid = uuid.UUID(session_id) if isinstance(session_id, str) else session_id

            # Get session with messages
            stmt = select(ChatSession).options(
                selectinload(ChatSession.messages)
            ).where(ChatSession.id == session_uuid)
            result = await db.execute(stmt)
            session = result.scalar_one()

            # Get user profile for context
            profile = None
            if hasattr(self, 'memory_service'):
                from app.models.user import Profile
                # SQLite stores UUIDs as strings, so compare as strings
                stmt_profile = select(Profile).where(Profile.user_id == user_id)
                result_profile = await db.execute(stmt_profile)
                profile_obj = result_profile.scalar_one_or_none()
                if profile_obj:
                    profile = {
                        "party_name": profile_obj.party_name,
                        "other_party_name": profile_obj.other_party_name,
                        "case_number": profile_obj.case_number,
                        "children_info": profile_obj.children_info
                    }

            # Update memory if service available
            if hasattr(self, 'memory_service') and session.messages:
                messages_for_memory = [
                    {"sender": msg.sender.value, "content": msg.content}
                    for msg in session.messages
                ]
                memory = await self.memory_service.update_memory(
                    session_id, messages_for_memory, profile
                )

                # Apply reference resolution to user message
                if memory.entity_references:
                    resolved_message = self.memory_service.resolve_references(
                        user_message, memory.entity_references
                    )
                    logger.info(f"Resolved references: '{user_message}' -> '{resolved_message}'")
                else:
                    resolved_message = user_message
            else:
                resolved_message = user_message

            # Save user message
            user_msg = await self.add_message(
                db, session_id, user_message, MessageSender.USER
            )

            # Extract intent and entities (using resolved message)
            intent, entities, confidence = await self._extract_intent_entities(
                resolved_message, session
            )

            # Update message with extracted info
            user_msg.intent_detected = intent
            user_msg.entities = entities
            user_msg.confidence = confidence

            # Update session context with memory-enhanced information
            session.context = {
                **session.context,
                **entities,
                "last_intent": intent
            }

            # Add memory facts to context
            if hasattr(self, 'memory_service'):
                memory_context = self.memory_service.get_memory_context(session_id)
                if memory_context:
                    session.context["memory_facts"] = memory_context["facts"]

            if not session.intent and confidence > 70:
                session.intent = intent
                session.confidence_score = confidence

            # Generate response based on current state and intent
            response_content, new_state, quick_replies = await self._generate_response(
                session, user_message, intent, entities, db
            )

            # Update session state
            session.current_state = new_state

            # Save assistant response
            assistant_msg = await self.add_message(
                db, session_id, response_content,
                MessageSender.ASSISTANT,
                quick_replies=quick_replies
            )

            await db.commit()

            return {
                "success": True,
                "message": {
                    "id": str(assistant_msg.id),
                    "content": response_content,
                    "sender": "assistant",
                    "quick_replies": quick_replies,
                    "timestamp": assistant_msg.created_at.isoformat()
                },
                "session": {
                    "id": str(session.id),
                    "state": session.current_state.value,
                    "intent": session.intent,
                    "confidence": session.confidence_score
                }
            }

        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def _extract_intent_entities(
        self,
        message: str,
        session: ChatSession
    ) -> Tuple[str, Dict, int]:
        """Extract intent and entities from user message"""

        # Use LLM if available for better accuracy
        if self.use_llm and self.llm_chat_service:
            try:
                # Build conversation history for context
                conversation_history = []
                if hasattr(session, 'messages') and session.messages:
                    conversation_history = [
                        {"sender": msg.sender.value, "content": msg.content}
                        for msg in session.messages[-5:]  # Last 5 messages
                    ]

                # Get LLM classification
                intent, entities, confidence_float = await self.llm_chat_service.classify_intent(
                    message, conversation_history
                )

                # Convert confidence to percentage
                confidence = int(confidence_float * 100)

                logger.info(f"LLM classified intent: {intent} with confidence {confidence}%")
                return intent, entities, confidence

            except Exception as e:
                logger.error(f"LLM intent extraction failed, falling back to patterns: {e}")
                # Fall through to pattern-based extraction

        # Fallback to pattern-based extraction
        message_lower = message.lower()

        # Check patterns for basic intent
        detected_intent = None
        confidence = 0

        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, message_lower):
                    detected_intent = intent
                    confidence = 80
                    break
            if detected_intent:
                break

        # Extract entities
        entities = {}

        # Extract motion type mentions
        if "custody" in message_lower:
            entities["motion_type"] = "custody"
        elif "support" in message_lower:
            entities["motion_type"] = "support"
        elif "violation" in message_lower:
            entities["motion_type"] = "violation"
        elif "emergency" in message_lower or "ex parte" in message_lower:
            entities["urgency"] = "emergency"

        # Extract dates
        date_patterns = r'\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b'
        dates = re.findall(date_patterns, message)
        if dates:
            entities["mentioned_dates"] = dates

        # Extract names (simple capitalized words for now)
        name_pattern = r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b'
        names = re.findall(name_pattern, message)
        if names:
            entities["mentioned_names"] = names

        # Extract money amounts
        money_pattern = r'\$[\d,]+(?:\.\d{2})?'
        amounts = re.findall(money_pattern, message)
        if amounts:
            entities["mentioned_amounts"] = amounts

        # Use context for better detection
        if not detected_intent and session.intent:
            detected_intent = session.intent
            confidence = 60

        return detected_intent or "UNKNOWN", entities, confidence

    async def _generate_response(
        self,
        session: ChatSession,
        user_message: str,
        intent: str,
        entities: Dict,
        db: AsyncSession
    ) -> Tuple[str, ChatSessionState, List[str]]:
        """Generate appropriate response based on state and context"""

        # Try LLM-generated response first if available
        if self.use_llm and self.llm_chat_service:
            try:
                # Generate contextual response using LLM
                response, quick_replies = await self.llm_chat_service.generate_contextual_response(
                    session.current_state,
                    user_message,
                    intent,
                    entities,
                    session.context
                )

                # Determine next state based on intent and current state
                new_state = self._determine_next_state(session.current_state, intent, entities)

                logger.info(f"LLM generated response with {len(quick_replies)} quick replies")
                return response, new_state, quick_replies

            except Exception as e:
                logger.error(f"LLM response generation failed, using rule-based: {e}")
                # Fall through to rule-based response

        current_state = session.current_state
        quick_replies = []

        # State machine for conversation flow
        if current_state == ChatSessionState.GREETING:
            if intent == "FILE_MOTION":
                response = "I can help you file a motion. What type of order are you seeking?"
                new_state = ChatSessionState.MOTION_SELECTION
                quick_replies = self.quick_replies[ChatSessionState.MOTION_SELECTION]

            elif intent == "RESPOND_MOTION":
                response = "I can help you respond to court papers. Do you have the papers with you?"
                new_state = ChatSessionState.MOTION_SELECTION
                quick_replies = ["Yes, I have them", "No, but I know what they say", "I need to get them"]

            elif intent == "GET_HELP":
                response = "I'm here to help you with California family court motions. I can help you file new requests or respond to papers you've received. What would you like to do?"
                new_state = ChatSessionState.GREETING
                quick_replies = self.quick_replies[ChatSessionState.GREETING]

            else:
                response = "Hello! I'm here to help you with California family court motions. Would you like to file a new request or respond to papers you've received?"
                new_state = ChatSessionState.GREETING
                quick_replies = self.quick_replies[ChatSessionState.GREETING]

        elif current_state == ChatSessionState.MOTION_SELECTION:
            motion_type = entities.get("motion_type")

            if motion_type == "violation":
                response = await self._handle_violation_flow(session, entities, db)
                new_state = ChatSessionState.INFORMATION_GATHERING
                quick_replies = ["It's an emergency", "It's not urgent", "I'm not sure"]

            elif motion_type == "custody":
                response = "I'll help you with a custody order. Are you requesting a new order or modifying an existing one?"
                new_state = ChatSessionState.INFORMATION_GATHERING
                quick_replies = ["New custody order", "Modify existing order", "Emergency custody change"]

            elif motion_type == "support":
                response = "I'll help you with support orders. Are you requesting child support, spousal support, or both?"
                new_state = ChatSessionState.INFORMATION_GATHERING
                quick_replies = ["Child support only", "Spousal support only", "Both"]

            else:
                response = "What type of order do you need help with? I can assist with custody, support, violations, or other family law matters."
                new_state = ChatSessionState.MOTION_SELECTION
                quick_replies = self.quick_replies[ChatSessionState.MOTION_SELECTION]

        elif current_state == ChatSessionState.INFORMATION_GATHERING:
            # Check if we have enough information
            if await self._has_sufficient_information(session):
                response = "Great! I have the information I need. Let me prepare your documents. This will take a moment..."
                new_state = ChatSessionState.PDF_GENERATION
                quick_replies = ["Review my information", "Add more details"]
            else:
                # Ask next required question
                response = await self._get_next_question(session, db)
                new_state = ChatSessionState.INFORMATION_GATHERING
                quick_replies = []  # Context-specific

        else:
            response = "I'm tracking our conversation. Please continue telling me about your situation."
            new_state = current_state
            quick_replies = ["Start over", "Get help"]

        return response, new_state, quick_replies

    async def _handle_violation_flow(
        self,
        session: ChatSession,
        entities: Dict,
        db: AsyncSession
    ) -> str:
        """Handle violation-specific conversation flow"""
        session.motion_type_detected = "VIOLATION"

        # Check urgency
        if entities.get("urgency") == "emergency":
            return "I understand this is urgent. For emergency violations, we can file an ex parte motion for immediate relief. Can you tell me what court order was violated and when?"
        else:
            return "I'll help you report a violation of a court order. What type of order was violated - custody, support, or another type?"

    async def _has_sufficient_information(self, session: ChatSession) -> bool:
        """Check if we have enough information to proceed"""
        required_fields = {
            "custody": ["current_arrangement", "requested_change", "reason"],
            "support": ["current_amount", "requested_amount", "change_reason"],
            "violation": ["order_violated", "violation_date", "description"]
        }

        motion_type = session.context.get("motion_type")
        if not motion_type:
            return False

        required = required_fields.get(motion_type, [])
        for field in required:
            if field not in session.context:
                return False

        return True

    async def _get_next_question(self, session: ChatSession, db: AsyncSession) -> str:
        """Get the next question to ask based on what we know"""
        context = session.context
        motion_type = context.get("motion_type", "")

        # Load user profile for auto-fill
        stmt = select(Profile).where(Profile.user_id == session.user_id)
        result = await db.execute(stmt)
        profile = result.scalar_one_or_none()

        questions = {
            "custody": [
                ("current_arrangement", "What is the current custody arrangement?"),
                ("requested_change", "What changes are you requesting?"),
                ("reason", "Why are you requesting this change?"),
                ("best_interest", "How will this benefit the children?")
            ],
            "support": [
                ("current_amount", "What is the current support amount?"),
                ("requested_amount", "What amount are you requesting?"),
                ("change_reason", "What has changed that requires this modification?"),
                ("income_change", "Has there been a change in income?")
            ],
            "violation": [
                ("order_violated", "What court order was violated?"),
                ("violation_date", "When did the violation occur?"),
                ("description", "Please describe what happened in detail."),
                ("evidence", "Do you have evidence of the violation?")
            ]
        }

        # Get questions for this motion type
        motion_questions = questions.get(motion_type, [])

        # Find next unanswered question
        for field, question in motion_questions:
            if field not in context:
                # Check if we can auto-fill from profile
                if profile and hasattr(profile, field):
                    context[field] = getattr(profile, field)
                    continue
                return question

        return "Can you provide any additional details about your situation?"

    def _get_greeting_message(self, initial_message: Optional[str] = None) -> str:
        """Generate appropriate greeting message"""
        if initial_message:
            return f"Hello! I see you're interested in help with: '{initial_message}'. I'm here to guide you through the California family court process. How can I assist you today?"
        else:
            return "Hello! I'm your California family court assistant. I can help you file motions, respond to court papers, or answer questions about the process. What would you like help with today?"

    async def get_session_history(
        self,
        db: AsyncSession,
        session_id: str,
        limit: int = 50
    ) -> List[Dict]:
        """Get message history for a session"""
        stmt = select(ChatMessage).where(
            ChatMessage.session_id == session_id
        ).order_by(ChatMessage.created_at).limit(limit)

        result = await db.execute(stmt)
        messages = result.scalars().all()

        return [
            {
                "id": str(msg.id),
                "content": msg.content,
                "sender": msg.sender.value,
                "timestamp": msg.created_at.isoformat(),
                "quick_replies": msg.quick_replies,
                "attachments": msg.attachments
            }
            for msg in messages
        ]

    async def get_active_sessions(
        self,
        db: AsyncSession,
        user_id: str
    ) -> List[ChatSession]:
        """Get all active sessions for a user"""
        # SQLite stores UUIDs as strings, so compare as strings
        stmt = select(ChatSession).where(
            and_(
                ChatSession.user_id == user_id,
                ChatSession.status == ChatSessionStatus.ACTIVE
            )
        ).order_by(desc(ChatSession.last_message_at))

        result = await db.execute(stmt)
        return result.scalars().all()

    async def complete_session(
        self,
        db: AsyncSession,
        session_id: str
    ) -> bool:
        """Mark a session as completed"""
        import uuid
        # Convert string session_id to UUID for query
        session_uuid = uuid.UUID(session_id) if isinstance(session_id, str) else session_id

        stmt = select(ChatSession).where(ChatSession.id == session_uuid)
        result = await db.execute(stmt)
        session = result.scalar_one_or_none()

        if session:
            session.status = ChatSessionStatus.COMPLETED
            session.completed_at = datetime.utcnow()
            await db.commit()
            return True
        return False

    def _determine_next_state(
        self,
        current_state: ChatSessionState,
        intent: str,
        entities: Dict
    ) -> ChatSessionState:
        """Determine the next conversation state based on intent and entities"""

        # State transition logic
        if current_state == ChatSessionState.GREETING:
            if intent in ["FILE_MOTION", "RESPOND_MOTION", "MODIFY_ORDER", "REPORT_VIOLATION"]:
                return ChatSessionState.MOTION_SELECTION
            elif intent == "GET_HELP":
                return ChatSessionState.GREETING  # Stay in greeting for help
            else:
                return current_state

        elif current_state == ChatSessionState.MOTION_SELECTION:
            if entities.get("motion_type"):
                return ChatSessionState.INFORMATION_GATHERING
            else:
                return current_state

        elif current_state == ChatSessionState.INFORMATION_GATHERING:
            # Check if we have enough information (this would need more logic)
            # For now, stay in information gathering
            return current_state

        else:
            return current_state
# Create global instance
chat_service = ChatService()
