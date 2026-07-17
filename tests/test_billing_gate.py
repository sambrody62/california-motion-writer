"""
Entitlement gate: LLM drafting and PDF export require an active subscription
(402 subscription_required) when BILLING_ENABLED=true.
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import select

from app.main import app
from app.core.database import Base, get_db
from app.core.entitlements import is_entitled
from app.models.subscription import Subscription
from app.models.user import User

pytestmark = pytest.mark.asyncio

REWRITE_BODY = {"motion_type": "RFO", "section": "facts", "user_input": "test input"}


@pytest_asyncio.fixture
async def billing_client():
    """Client plus a session maker into the same in-memory DB, so tests can
    insert subscription rows for API-registered users."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False, future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async def override_get_db():
        async with session_maker() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac, session_maker
    app.dependency_overrides.clear()
    await engine.dispose()


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
async def test_unsubscribed_user_gets_402(billing_client, monkeypatch, method, path, body):
    monkeypatch.setenv("BILLING_ENABLED", "true")
    client, _ = billing_client
    headers = await _register_and_login(client)
    kwargs = {"headers": headers} if body is None else {"headers": headers, "json": body}
    response = await getattr(client, method)(path, **kwargs)
    assert response.status_code == 402
    assert response.json()["detail"]["code"] == "subscription_required"


async def test_active_subscription_passes_gate(billing_client, monkeypatch):
    monkeypatch.setenv("BILLING_ENABLED", "true")
    client, session_maker = billing_client
    headers = await _register_and_login(client)
    await _set_subscription(session_maker, "active")
    response = await client.post("/api/v1/llm/rewrite", headers=headers, json=REWRITE_BODY)
    assert response.status_code != 402


async def test_canceled_subscription_gets_402(billing_client, monkeypatch):
    monkeypatch.setenv("BILLING_ENABLED", "true")
    client, session_maker = billing_client
    headers = await _register_and_login(client)
    await _set_subscription(session_maker, "canceled")
    response = await client.post("/api/v1/llm/rewrite", headers=headers, json=REWRITE_BODY)
    assert response.status_code == 402


async def test_gate_disabled_by_default_flag(billing_client):
    # conftest sets BILLING_ENABLED=false — existing behavior is untouched
    client, _ = billing_client
    headers = await _register_and_login(client)
    response = await client.post("/api/v1/llm/rewrite", headers=headers, json=REWRITE_BODY)
    assert response.status_code != 402
