"""
Subscription model — Stripe billing state, one row per user
"""
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, BigInteger
from app.core.uuid_type import UUID
from sqlalchemy.orm import relationship
import uuid

from app.core.database import Base


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(UUID(), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(
        UUID(),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    stripe_customer_id = Column(String(255), nullable=False, index=True)
    stripe_subscription_id = Column(String(255), unique=True, index=True)

    # Verbatim Stripe status snapshot (active, trialing, past_due, canceled, ...)
    status = Column(String(50), nullable=False, default="incomplete")
    price_id = Column(String(255))
    current_period_end = Column(DateTime(timezone=True))
    cancel_at_period_end = Column(Boolean, nullable=False, default=False)

    # Stripe event.created of the last applied webhook event — guards
    # against out-of-order delivery regressing newer state
    last_event_created = Column(BigInteger)

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="subscription")
