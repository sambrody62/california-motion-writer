"""
Motion and Draft models
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, JSON, Text, Integer, Date, Time
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from app.core.database import Base

class Motion(Base):
    __tablename__ = "motions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    profile_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id"))
    
    # Motion Details
    motion_type = Column(String(50), nullable=False)  # 'RFO', 'RESPONSE'
    status = Column(String(50), nullable=False, default="draft")  # draft, completed, filed
    case_caption = Column(Text)
    
    # Filing Info
    filing_date = Column(Date)
    hearing_date = Column(Date)
    hearing_time = Column(Time)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, index=True)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime(timezone=True))
    
    # Relationships
    user = relationship("User", back_populates="motions")
    drafts = relationship("MotionDraft", back_populates="motion", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="motion", cascade="all, delete-orphan")

class MotionDraft(Base):
    __tablename__ = "motion_drafts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    motion_id = Column(UUID(as_uuid=True), ForeignKey("motions.id", ondelete="CASCADE"), nullable=False)
    
    # Q&A Data
    step_number = Column(Integer, nullable=False)
    step_name = Column(String(100))  # 'relief_requested', 'facts', etc.
    question_data = Column(JSON)  # Original Q&A
    
    # LLM Processing
    llm_input = Column(Text)  # Context sent to LLM
    llm_output = Column(Text)  # Rewritten text
    llm_model = Column(String(50))
    llm_tokens_used = Column(Integer)
    
    # Status
    is_complete = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    motion = relationship("Motion", back_populates="drafts")

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    motion_id = Column(UUID(as_uuid=True), ForeignKey("motions.id", ondelete="CASCADE"), nullable=False)
    
    # Document Info
    document_type = Column(String(50), nullable=False)  # 'FL-300', 'FL-320'
    filename = Column(String(255), nullable=False)
    gcs_url = Column(Text, nullable=False)
    file_size_bytes = Column(Integer)
    pages = Column(Integer)
    
    # Generation
    generated_at = Column(DateTime(timezone=True), default=datetime.utcnow, index=True)
    generation_method = Column(String(50))  # 'automated', 'manual_edit'
    
    # Relationships
    motion = relationship("Motion", back_populates="documents")