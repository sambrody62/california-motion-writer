"""
Evidence model
"""
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, JSON, Text, Date
from sqlalchemy.orm import relationship
import uuid

from app.core.database import Base
from app.core.uuid_type import UUID


class Evidence(Base):
    __tablename__ = "evidence"

    id = Column(UUID(), primary_key=True, default=lambda: str(uuid.uuid4()))
    motion_id = Column(UUID(), ForeignKey("motions.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Evidence details
    evidence_type = Column(String(50), nullable=False)  # text, email, photo, document
    tags = Column(JSON, nullable=False, default=list)
    source_date = Column(Date, nullable=True)
    description = Column(Text, nullable=False)
    transcription = Column(Text, nullable=True)

    # File storage
    filename = Column(String(255), nullable=True)
    storage_path = Column(Text, nullable=True)

    # Confirmation flag — must be True before text content is used in a motion
    user_confirmed = Column(Boolean, nullable=False, default=False)

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, index=True)

    # Relationships
    motion = relationship("Motion", back_populates="evidence")
    user = relationship("User")
