"""
Rate limits must actually be enforced on expensive routes (LLM, PDF, auth).
"""
import pytest
from httpx import AsyncClient

from app.middleware.rate_limiter import rate_limiter

pytestmark = pytest.mark.asyncio


@pytest.fixture
def rate_limits_on(monkeypatch):
    monkeypatch.setenv("RATE_LIMIT_ENABLED", "true")
    rate_limiter.memory_store.clear()
    yield
    rate_limiter.memory_store.clear()


async def test_llm_process_motion_throttled_after_limit(
    client: AsyncClient, auth_headers: dict, rate_limits_on
):
    # /api/v1/llm/process-motion is limited to 5/hour
    statuses = []
    for _ in range(6):
        resp = await client.post(
            "/api/v1/llm/process-motion",
            json={"motion_id": "00000000-0000-0000-0000-000000000000"},
            headers=auth_headers,
        )
        statuses.append(resp.status_code)

    assert all(status != 429 for status in statuses[:5])
    assert statuses[5] == 429


async def test_429_carries_retry_after_header(
    client: AsyncClient, auth_headers: dict, rate_limits_on
):
    # exhaust the 5/hour process-motion limit, then inspect the 429
    for _ in range(5):
        await client.post(
            "/api/v1/llm/process-motion",
            json={"motion_id": "00000000-0000-0000-0000-000000000000"},
            headers=auth_headers,
        )
    resp = await client.post(
        "/api/v1/llm/process-motion",
        json={"motion_id": "00000000-0000-0000-0000-000000000000"},
        headers=auth_headers,
    )

    assert resp.status_code == 429
    retry_after = int(resp.headers["retry-after"])
    assert 0 < retry_after <= 3600


async def test_auth_token_throttled_after_limit(client: AsyncClient, rate_limits_on):
    # /api/v1/auth/token is limited to 20/hour
    for _ in range(20):
        resp = await client.post(
            "/api/v1/auth/token",
            data={"username": "nobody@example.com", "password": "wrong"},
        )
        assert resp.status_code != 429

    resp = await client.post(
        "/api/v1/auth/token",
        data={"username": "nobody@example.com", "password": "wrong"},
    )
    assert resp.status_code == 429


async def test_unlisted_paths_are_not_throttled(client: AsyncClient, rate_limits_on):
    # No catch-all default limit — ordinary routes stay unthrottled
    for _ in range(30):
        resp = await client.get("/health")
        assert resp.status_code == 200


async def test_kill_switch_disables_limits(
    client: AsyncClient, auth_headers: dict, monkeypatch
):
    monkeypatch.setenv("RATE_LIMIT_ENABLED", "false")
    rate_limiter.memory_store.clear()

    for _ in range(10):
        resp = await client.post(
            "/api/v1/llm/process-motion",
            json={"motion_id": "00000000-0000-0000-0000-000000000000"},
            headers=auth_headers,
        )
        assert resp.status_code != 429
