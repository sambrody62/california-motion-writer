"""
Import all models to ensure they're registered with SQLAlchemy
"""
from app.models.user import User, Profile
from app.models.motion import Motion
from app.models.chat import (
    ChatSession,
    ChatMessage,
    ChatIntent,
    ConversationTemplate
)
from app.models.evidence import Evidence

__all__ = [
    'User',
    'Profile',
    'Motion',
    'ChatSession',
    'ChatMessage',
    'ChatIntent',
    'ConversationTemplate',
    'Evidence',
]