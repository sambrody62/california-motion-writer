"""
POST /webhooks/stripe: signature verification and event application
"""
import hashlib
import hmac
import json
import time

import pytest
from sqlalchemy import select

from app.core.config import settings
from app.models.subscription import Subscription
from app.models.user import User

pytestmark = pytest.mark.asyncio

WEBHOOK_SECRET = "whsec_test_secret"
WEBHOOK_PATH = "/api/v1/webhooks/stripe"


@pytest.fixture
def webhook_secret(monkeypatch):
    monkeypatch.setattr(settings, "STRIPE_WEBHOOK_SECRET", WEBHOOK_SECRET)


def _sign(payload: bytes, secret: str = WEBHOOK_SECRET, timestamp: int = None) -> str:
    timestamp = timestamp or int(time.time())
    signed = f"{timestamp}.".encode() + payload
    signature = hmac.new(secret.encode(), signed, hashlib.sha256).hexdigest()
    return f"t={timestamp},v1={signature}"


def _event_payload(created=100, status="active") -> bytes:
    return json.dumps({
        "id": "evt_1",
        "object": "event",
        "type": "customer.subscription.updated",
        "created": created,
        "data": {"object": {
            "id": "sub_1",
            "customer": "cus_1",
            "status": status,
            "current_period_end": 1893456000,
            "cancel_at_period_end": False,
            "items": {"data": [{"price": {"id": "price_test"}}]},
        }},
    }).encode()


async def _seed_subscription(session_maker, status="incomplete"):
    async with session_maker() as session:
        user = User(email="hook@example.com", password_hash="x", full_name="Hook User")
        session.add(user)
        await session.commit()
        await session.refresh(user)
        session.add(Subscription(
            user_id=user.id, stripe_customer_id="cus_1", status=status
        ))
        await session.commit()


async def _row_status(session_maker) -> str:
    async with session_maker() as session:
        row = (await session.execute(select(Subscription))).scalar_one()
        return row.status


async def test_missing_signature_rejected(client_with_db, webhook_secret):
    client, _ = client_with_db
    response = await client.post(WEBHOOK_PATH, content=_event_payload())
    assert response.status_code == 400


async def test_invalid_signature_rejected(client_with_db, webhook_secret):
    client, session_maker = client_with_db
    await _seed_subscription(session_maker)
    payload = _event_payload()
    response = await client.post(
        WEBHOOK_PATH,
        content=payload,
        headers={"stripe-signature": _sign(payload, secret="whsec_wrong")},
    )
    assert response.status_code == 400
    assert await _row_status(session_maker) == "incomplete"


async def test_valid_signature_applies_event(client_with_db, webhook_secret):
    # No Authorization header — the webhook must not require JWT auth
    client, session_maker = client_with_db
    await _seed_subscription(session_maker)
    payload = _event_payload(created=100, status="active")
    response = await client.post(
        WEBHOOK_PATH, content=payload, headers={"stripe-signature": _sign(payload)}
    )
    assert response.status_code == 200
    assert response.json() == {"received": True}
    assert await _row_status(session_maker) == "active"


async def test_replayed_event_is_harmless(client_with_db, webhook_secret):
    client, session_maker = client_with_db
    await _seed_subscription(session_maker)
    payload = _event_payload(created=100, status="active")
    for _ in range(2):
        response = await client.post(
            WEBHOOK_PATH, content=payload, headers={"stripe-signature": _sign(payload)}
        )
        assert response.status_code == 200
    assert await _row_status(session_maker) == "active"


async def test_stale_event_does_not_regress(client_with_db, webhook_secret):
    client, session_maker = client_with_db
    await _seed_subscription(session_maker)
    newer = _event_payload(created=200, status="canceled")
    await client.post(WEBHOOK_PATH, content=newer, headers={"stripe-signature": _sign(newer)})
    older = _event_payload(created=150, status="active")
    response = await client.post(
        WEBHOOK_PATH, content=older, headers={"stripe-signature": _sign(older)}
    )
    assert response.status_code == 200
    assert await _row_status(session_maker) == "canceled"
