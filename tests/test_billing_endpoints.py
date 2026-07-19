"""
Billing endpoints: checkout-session, portal-session, status, verify-session
"""
from unittest.mock import patch

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.core.config import settings
from app.models.subscription import Subscription
from app.models.user import User

pytestmark = pytest.mark.asyncio


async def _register_and_login(client: AsyncClient) -> dict:
    await client.post("/api/v1/auth/register", json={
        "email": "payer@example.com",
        "password": "payerpass123",
        "full_name": "Payer User",
    })
    response = await client.post(
        "/api/v1/auth/token",
        data={"username": "payer@example.com", "password": "payerpass123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


async def _user_id(session_maker) -> str:
    async with session_maker() as session:
        result = await session.execute(select(User).where(User.email == "payer@example.com"))
        return str(result.scalar_one().id)


async def _add_subscription(session_maker, status="active", **kwargs):
    async with session_maker() as session:
        result = await session.execute(select(User).where(User.email == "payer@example.com"))
        user = result.scalar_one()
        session.add(Subscription(
            user_id=user.id,
            stripe_customer_id=kwargs.pop("stripe_customer_id", "cus_1"),
            status=status,
            **kwargs,
        ))
        await session.commit()


@pytest.mark.parametrize("method,path", [
    ("post", "/api/v1/billing/checkout-session"),
    ("post", "/api/v1/billing/portal-session"),
    ("get", "/api/v1/billing/status"),
    ("post", "/api/v1/billing/verify-session"),
])
async def test_billing_requires_auth(client_with_db, method, path):
    client, _ = client_with_db
    response = await getattr(client, method)(path)
    assert response.status_code == 401


async def test_checkout_session_returns_url(client_with_db, monkeypatch):
    monkeypatch.setattr(settings, "STRIPE_SECRET_KEY", "sk_test_key")
    monkeypatch.setattr(settings, "STRIPE_PRICE_ID", "price_test")
    monkeypatch.setattr(settings, "STRIPE_SETUP_PRICE_ID", "price_setup")
    client, _ = client_with_db
    headers = await _register_and_login(client)
    with patch("app.services.stripe_service.stripe.Customer.create") as cus, \
         patch("app.services.stripe_service.stripe.checkout.Session.create") as ses:
        cus.return_value = {"id": "cus_new"}
        ses.return_value = {"url": "https://checkout.stripe.com/c/pay/x"}
        response = await client.post(
            "/api/v1/billing/checkout-session",
            headers=headers,
            json={"return_to": "/motion/1/preview"},
        )
    assert response.status_code == 200
    assert response.json() == {"url": "https://checkout.stripe.com/c/pay/x"}


async def test_checkout_session_503_when_unconfigured(client_with_db):
    # settings default STRIPE_SECRET_KEY is "" in tests
    client, _ = client_with_db
    headers = await _register_and_login(client)
    response = await client.post("/api/v1/billing/checkout-session", headers=headers, json={})
    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "billing_not_configured"


async def test_portal_session_404_without_subscription(client_with_db, monkeypatch):
    monkeypatch.setattr(settings, "STRIPE_SECRET_KEY", "sk_test_key")
    client, _ = client_with_db
    headers = await _register_and_login(client)
    response = await client.post("/api/v1/billing/portal-session", headers=headers)
    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "no_subscription"


async def test_portal_session_returns_url(client_with_db, monkeypatch):
    monkeypatch.setattr(settings, "STRIPE_SECRET_KEY", "sk_test_key")
    client, session_maker = client_with_db
    headers = await _register_and_login(client)
    await _add_subscription(session_maker)
    with patch("app.services.stripe_service.stripe.billing_portal.Session.create") as ses:
        ses.return_value = {"url": "https://billing.stripe.com/p/session/x"}
        response = await client.post("/api/v1/billing/portal-session", headers=headers)
    assert response.status_code == 200
    assert response.json() == {"url": "https://billing.stripe.com/p/session/x"}


async def test_status_no_subscription(client_with_db):
    client, _ = client_with_db
    headers = await _register_and_login(client)
    response = await client.get("/api/v1/billing/status", headers=headers)
    assert response.status_code == 200
    assert response.json() == {
        "status": None,
        "is_entitled": False,
        "current_period_end": None,
        "cancel_at_period_end": False,
    }


@pytest.mark.parametrize("status,entitled", [("active", True), ("canceled", False)])
async def test_status_reflects_subscription(client_with_db, status, entitled):
    client, session_maker = client_with_db
    headers = await _register_and_login(client)
    await _add_subscription(session_maker, status=status)
    response = await client.get("/api/v1/billing/status", headers=headers)
    body = response.json()
    assert body["status"] == status
    assert body["is_entitled"] is entitled


async def test_verify_session_syncs_subscription(client_with_db, monkeypatch):
    monkeypatch.setattr(settings, "STRIPE_SECRET_KEY", "sk_test_key")
    client, session_maker = client_with_db
    headers = await _register_and_login(client)
    await _add_subscription(session_maker, status="incomplete")
    user_id = await _user_id(session_maker)
    with patch("app.services.stripe_service.stripe.checkout.Session.retrieve") as ses, \
         patch("app.services.stripe_service.stripe.Subscription.retrieve") as sub:
        ses.return_value = {
            "id": "cs_1",
            "customer": "cus_1",
            "subscription": "sub_1",
            "client_reference_id": user_id,
        }
        sub.return_value = {
            "id": "sub_1",
            "customer": "cus_1",
            "status": "active",
            "current_period_end": 1893456000,
            "cancel_at_period_end": False,
            "items": {"data": [{"price": {"id": "price_test"}}]},
        }
        response = await client.post(
            "/api/v1/billing/verify-session", headers=headers, json={"session_id": "cs_1"}
        )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "active"
    assert body["is_entitled"] is True


async def test_verify_session_rejects_foreign_session(client_with_db, monkeypatch):
    monkeypatch.setattr(settings, "STRIPE_SECRET_KEY", "sk_test_key")
    client, _ = client_with_db
    headers = await _register_and_login(client)
    with patch("app.services.stripe_service.stripe.checkout.Session.retrieve") as ses:
        ses.return_value = {"id": "cs_1", "client_reference_id": "someone-else"}
        response = await client.post(
            "/api/v1/billing/verify-session", headers=headers, json={"session_id": "cs_1"}
        )
    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "session_ownership_mismatch"
