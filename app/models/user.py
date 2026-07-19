"""
User and Profile models
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, JSON, Text
from app.core.uuid_type import UUID
from sqlalchemy.orm import relationship
import uuid

from app.core.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    phone = Column(String(20))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime(timezone=True))
    is_active = Column(Boolean, default=True)
    email_verified = Column(Boolean, default=False)
    
    # Relationships
    profile = relationship("Profile", back_populates="user", uselist=False)
    motions = relationship("Motion", back_populates="user")
    chat_sessions = relationship("ChatSession", back_populates="user")
    subscription = relationship("Subscription", back_populates="user", uselist=False)

class Profile(Base):
    __tablename__ = "profiles"
    
    id = Column(UUID(), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(UUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    
    # Case Information
    case_number = Column(String(50))
    county = Column(String(100))  # Made optional
    court_branch = Column(String(255))
    department = Column(String(50))

    # Party Information
    is_petitioner = Column(Boolean, default=True)  # Made optional with default
    party_name = Column(String(255))  # Made optional
    party_address = Column(Text)
    party_phone = Column(String(20))

    # Filer Location
    city = Column(String(100), nullable=True)
    zip_code = Column(String(20), nullable=True)
    state = Column(String(50), nullable=True, default="CA")

    # Other Party
    other_party_name = Column(String(255))  # Made optional
    other_party_address = Column(Text)
    other_party_attorney = Column(String(255))
    
    # Children (JSON array)
    children_info = Column(JSON)  # [{name, dob, current_custody}]
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="profile")