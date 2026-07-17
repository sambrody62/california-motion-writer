"""
Tests for Stripe billing settings
"""
from app.core.config import settings


def test_stripe_settings_have_safe_defaults():
    assert settings.STRIPE_SECRET_KEY == ""
    assert settings.STRIPE_WEBHOOK_SECRET == ""
    assert settings.STRIPE_PRICE_ID == ""
    assert settings.FRONTEND_URL == "http://localhost:3000"
