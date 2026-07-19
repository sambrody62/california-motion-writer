"""
Entitlement gate: LLM drafting and PDF export require an active subscription
(402 subscription_required) when BILLING_ENABLED=true.
"""
import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.core.entitlements import is_entitled
from app.models.subscription import Subscription
from app.models.user import User

pytestmark = pytest.mark.asyncio

REWRITE_BODY = {"motion_type": "RFO", "section": "facts", "user_input": "test input"}


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


async def _set_subscription(session_maker, status: str):
    async with session_maker() as session:
        result = await session.execute(
            select(User).where(User.email == "payer@example.com")
        )
        user = result.scalar_one()
        existing = (
            await session.execute(
                select(Subscription).where(Subscription.user_id == user.id)
            )
        ).scalar_one_or_none()
        if existing:
            existing.status = status
        else:
            session.add(
                Subscription(user_id=user.id, stripe_customer_id="cus_test", status=status)
            )
        await session.commit()


def test_is_entitled_truth_table():
    assert is_entitled(None) is False
    for status in ("incomplete", "canceled", "unpaid", "incomplete_expired", "paused"):
        assert is_entitled(Subscription(status=status)) is False, status
    for status in ("active", "trialing", "past_due"):
        assert is_entitled(Subscription(status=status)) is True, status


GATED_CALLS = [
    ("post", "/api/v1/llm/rewrite", REWRITE_BODY),
    ("post", "/api/v1/documents/generate-pdf-sync", {"motion_id": "00000000-0000-0000-0000-000000000000"}),
    ("post", "/api/v1/documents/generate-pdf", {"motion_id": "00000000-0000-0000-0000-000000000000"}),
    ("get", "/api/v1/documents/00000000-0000-0000-0000-000000000000/download", None),
    ("post", "/api/v1/chat-pdf/generate-pdf", {"motion_id": "00000000-0000-0000-0000-000000000000"}),
    ("post", "/api/v1/chat-pdf/complete-workflow", {"session_id": "s1"}),
]


@pytest.mark.parametrize("method,path,body", GATED_CALLS)
async def test_unsubscribed_user_gets_402(client_with_db, monkeypatch, method, path, body):
    monkeypatch.setenv("BILLING_ENABLED", "true")
    client, _ = client_with_db
    headers = await _register_and_login(client)
    kwargs = {"headers": headers} if body is None else {"headers": headers, "json": body}
    response = await getattr(client, method)(path, **kwargs)
    assert response.status_code == 402
    assert response.json()["detail"]["code"] == "subscription_required"


async def test_active_subscription_passes_gate(client_with_db, monkeypatch):
    monkeypatch.setenv("BILLING_ENABLED", "true")
    client, session_maker = client_with_db
    headers = await _register_and_login(client)
    await _set_subscription(session_maker, "active")
    response = await client.post("/api/v1/llm/rewrite", headers=headers, json=REWRITE_BODY)
    assert response.status_code != 402


async def test_canceled_subscription_gets_402(client_with_db, monkeypatch):
    monkeypatch.setenv("BILLING_ENABLED", "true")
    client, session_maker = client_with_db
    headers = await _register_and_login(client)
    await _set_subscription(session_maker, "canceled")
    response = await client.post("/api/v1/llm/rewrite", headers=headers, json=REWRITE_BODY)
    assert response.status_code == 402


async def test_gate_disabled_by_default_flag(client_with_db):
    # conftest sets BILLING_ENABLED=false — existing behavior is untouched
    client, _ = client_with_db
    headers = await _register_and_login(client)
    response = await client.post("/api/v1/llm/rewrite", headers=headers, json=REWRITE_BODY)
    assert response.status_code != 402
