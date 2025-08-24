"""
Document model for generated PDFs
"""
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from app.core.database import Base

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    motion_id = Column(UUID(as_uuid=True), ForeignKey("motions.id", ondelete="CASCADE"), nullable=False)
    
    # Document Info
    document_type = Column(String(50), nullable=False)  # 'FL-300', 'FL-320', etc.
    filename = Column(String(255), nullable=False)
    gcs_url = Column(String, nullable=False)  # Google Cloud Storage URL
    file_size_bytes = Column(Integer)
    pages = Column(Integer)
    
    # Generation
    generated_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    generation_method = Column(String(50))  # 'automated', 'manual_edit'
    
    # Relationships
    motion = relationship("Motion", back_populates="documents")