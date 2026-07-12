"""
Chat session and message models for conversational interface
"""
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, JSON, Text, Integer, Enum as SQLEnum, Index
from sqlalchemy.orm import relationship
import uuid
import enum

from app.core.database import Base
from app.core.uuid_type import UUID

class ChatSessionStatus(enum.Enum):
    """Status of a chat session"""
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ABANDONED = "abandoned"

class ChatSessionState(enum.Enum):
    """Current state in the conversation flow"""
    GREETING = "greeting"
    INTENT_GATHERING = "intent_gathering"
    PROFILE_COLLECTION = "profile_collection"
    MOTION_SELECTION = "motion_selection"
    INFORMATION_GATHERING = "information_gathering"
    CLARIFICATION = "clarification"
    REVIEW = "review"
    PDF_GENERATION = "pdf_generation"
    COMPLETED = "completed"

class MessageSender(enum.Enum):
    """Who sent the message"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(UUID(), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(UUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Session info
    status = Column(SQLEnum(ChatSessionStatus), nullable=False, default=ChatSessionStatus.ACTIVE)
    current_state = Column(SQLEnum(ChatSessionState), nullable=False, default=ChatSessionState.GREETING)

    # Context and memory
    context = Column(JSON, default={})  # Stores extracted entities, intent, etc.
    memory_summary = Column(Text)  # Summarized context for long conversations

    # Motion being worked on (if applicable)
    motion_id = Column(UUID(), ForeignKey("motions.id", ondelete="SET NULL"))
    motion_type_detected = Column(String(50))  # What type of motion we think they need
    forms_identified = Column(JSON, default=[])  # List of form IDs needed

    # Conversation metadata
    intent = Column(String(100))  # Primary intent: FILE_MOTION, RESPOND, GET_INFO, etc.
    confidence_score = Column(Integer)  # 0-100 confidence in intent
    language = Column(String(10), default="en")

    # Timestamps
    started_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    last_message_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    completed_at = Column(DateTime(timezone=True))

    # Session settings
    is_voice_enabled = Column(Boolean, default=False)
    preferred_tone = Column(String(20), default="professional")  # professional, friendly, simple

    # Relationships
    user = relationship("User", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan", order_by="ChatMessage.created_at")
    motion = relationship("Motion", backref="chat_session")

    # Indexes for performance
    __table_args__ = (
        Index('idx_chat_sessions_user_status', 'user_id', 'status'),
        Index('idx_chat_sessions_last_message', 'last_message_at'),
    )

class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(UUID(), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(UUID(), ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False, index=True)

    # Message content
    content = Column(Text, nullable=False)
    sender = Column(SQLEnum(MessageSender), nullable=False)

    # For assistant messages
    prompt_tokens = Column(Integer)  # Tokens used in prompt
    completion_tokens = Column(Integer)  # Tokens in response
    model_used = Column(String(50))  # Which LLM model was used

    # Extracted information
    entities = Column(JSON, default={})  # Extracted entities from this message
    intent_detected = Column(String(100))  # Intent detected in this message
    confidence = Column(Integer)  # Confidence in extraction (0-100)

    # Message metadata
    is_error = Column(Boolean, default=False)
    error_message = Column(Text)
    requires_clarification = Column(Boolean, default=False)
    clarification_for = Column(UUID(as_uuid=True))  # References another message ID

    # UI hints
    quick_replies = Column(JSON, default=[])  # Suggested quick replies
    attachments = Column(JSON, default=[])  # File attachments or images

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True)
    edited_at = Column(DateTime(timezone=True))

    # Relationships
    session = relationship("ChatSession", back_populates="messages")

    # Indexes for performance
    __table_args__ = (
        Index('idx_chat_messages_session_created', 'session_id', 'created_at'),
    )

class ChatIntent(Base):
    """Predefined intents for better classification"""
    __tablename__ = "chat_intents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    intent_key = Column(String(50), unique=True, nullable=False)
    display_name = Column(String(100), nullable=False)
    description = Column(Text)

    # Training examples for this intent
    example_phrases = Column(JSON, default=[])

    # What forms/actions this intent triggers
    triggers_forms = Column(JSON, default=[])
    requires_profile = Column(Boolean, default=True)

    # Follow-up questions for this intent
    follow_up_questions = Column(JSON, default=[])

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

class ConversationTemplate(Base):
    """Reusable conversation templates for common scenarios"""
    __tablename__ = "conversation_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    template_key = Column(String(50), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text)

    # The conversation flow
    initial_message = Column(Text, nullable=False)
    questions_sequence = Column(JSON, default=[])  # Ordered list of questions

    # When to use this template
    applicable_intents = Column(JSON, default=[])
    applicable_forms = Column(JSON, default=[])

    # Usage tracking
    times_used = Column(Integer, default=0)
    success_rate = Column(Integer)  # Percentage of successful completions

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    is_active = Column(Boolean, default=True)