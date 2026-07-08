"""
Tests for Gmail evidence import feature (flag-gated).

Rule: GMAIL_EVIDENCE_ENABLED=false (default) → every endpoint returns 404.
      GMAIL_EVIDENCE_ENABLED=true → feature is live.
"""
import os
import pytest
import pytest_asyncio
from unittest.mock import MagicMock, patch, AsyncMock
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _create_motion(client: AsyncClient, headers: dict) -> str:
    resp = await client.post(
        "/api/v1/motions/",
        json={
            "motion_type": "RFO",
            "title": "Gmail Test Motion",
            "description": "For gmail evidence tests",
        },
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


# ---------------------------------------------------------------------------
# Flag OFF — every endpoint must 404
# ---------------------------------------------------------------------------

async def test_auth_url_returns_404_when_flag_off(client: AsyncClient, auth_headers: dict):
    """With GMAIL_EVIDENCE_ENABLED unset/false all endpoints must return 404."""
    assert os.getenv("GMAIL_EVIDENCE_ENABLED", "false") != "true"
    resp = await client.get("/api/v1/gmail/auth-url", headers=auth_headers)
    assert resp.status_code == 404


async def test_exchange_returns_404_when_flag_off(client: AsyncClient, auth_headers: dict):
    assert os.getenv("GMAIL_EVIDENCE_ENABLED", "false") != "true"
    resp = await client.post(
        "/api/v1/gmail/exchange-code",
        json={"code": "dummy-code"},
        headers=auth_headers,
    )
    assert resp.status_code == 404


async def test_scan_returns_404_when_flag_off(client: AsyncClient, auth_headers: dict):
    assert os.getenv("GMAIL_EVIDENCE_ENABLED", "false") != "true"
    resp = await client.post(
        "/api/v1/motions/some-id/gmail/scan",
        json={"access_token": "tok"},
        headers=auth_headers,
    )
    assert resp.status_code == 404


async def test_import_returns_404_when_flag_off(client: AsyncClient, auth_headers: dict):
    assert os.getenv("GMAIL_EVIDENCE_ENABLED", "false") != "true"
    resp = await client.post(
        "/api/v1/motions/some-id/gmail/import",
        json={"access_token": "tok", "message_ids": ["id1"]},
        headers=auth_headers,
    )
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Flag ON — functional tests
# ---------------------------------------------------------------------------

MOCK_CANDIDATES = [
    {
        "message_id": "abc123",
        "from": "other@example.com",
        "date": "2024-03-10",
        "subject": "Re: Custody schedule",
        "snippet": "I won't be bringing the kids back on time...",
    }
]

MOCK_BODIES = {
    "abc123": {
        "date": "2024-03-10",
        "from": "other@example.com",
        "subject": "Re: Custody schedule",
        "body_text": "I won't be bringing the kids back on time this weekend.",
    }
}


@pytest.fixture
def gmail_env(monkeypatch):
    """Enable Gmail feature flag and set required env vars."""
    monkeypatch.setenv("GMAIL_EVIDENCE_ENABLED", "true")
    monkeypatch.setenv("GMAIL_OAUTH_CLIENT_ID", "test-client-id")
    monkeypatch.setenv("GMAIL_OAUTH_CLIENT_SECRET", "test-client-secret")
    monkeypatch.setenv("GMAIL_OAUTH_REDIRECT_URI", "http://localhost:3000/callback")


async def test_auth_url_returns_url(client: AsyncClient, auth_headers: dict, gmail_env):
    """GET /evidence/gmail/auth-url returns a URL when flag is on."""
    with patch(
        "app.services.gmail_evidence_service.get_auth_url",
        return_value="https://accounts.google.com/o/oauth2/auth?test=1",
    ):
        resp = await client.get("/api/v1/gmail/auth-url", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "auth_url" in data
    assert data["auth_url"].startswith("https://")


async def test_exchange_returns_access_token(client: AsyncClient, auth_headers: dict, gmail_env):
    """POST /evidence/gmail/exchange returns an access_token (short-lived, not stored)."""
    with patch(
        "app.services.gmail_evidence_service.exchange_code",
        return_value="ya29.short-lived-token",
    ):
        resp = await client.post(
            "/api/v1/gmail/exchange-code",
            json={"code": "4/authcode"},
            headers=auth_headers,
        )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["access_token"] == "ya29.short-lived-token"


async def test_scan_returns_candidates(client: AsyncClient, auth_headers: dict, gmail_env):
    """POST /motions/{id}/evidence/gmail/scan returns message candidates."""
    motion_id = await _create_motion(client, auth_headers)

    with patch(
        "app.services.gmail_evidence_service.scan_emails",
        return_value=MOCK_CANDIDATES,
    ):
        resp = await client.post(
            f"/api/v1/motions/{motion_id}/gmail/scan",
            json={"access_token": "ya29.tok"},
            headers=auth_headers,
        )

    assert resp.status_code == 200
    results = resp.json()
    assert isinstance(results, list)
    assert len(results) == 1
    assert results[0]["message_id"] == "abc123"
    # snippet present, full body NOT returned in scan
    assert "snippet" in results[0]
    assert "body_text" not in results[0]


async def test_scan_enforces_ownership(client: AsyncClient, auth_headers: dict, gmail_env):
    """Another user cannot scan a motion they don't own."""
    motion_id = await _create_motion(client, auth_headers)

    # Create a second user
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "stranger@example.com",
            "password": "strangerpass123",
            "full_name": "Stranger",
            "phone": "000-000-0001",
        },
    )
    login_resp = await client.post(
        "/api/v1/auth/token",
        data={"username": "stranger@example.com", "password": "strangerpass123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    other_headers = {"Authorization": f"Bearer {login_resp.json()['access_token']}"}

    resp = await client.post(
        f"/api/v1/motions/{motion_id}/gmail/scan",
        json={"access_token": "ya29.tok"},
        headers=other_headers,
    )
    assert resp.status_code == 404


async def test_import_creates_unconfirmed_evidence(client: AsyncClient, auth_headers: dict, gmail_env):
    """POST /motions/{id}/evidence/gmail/import creates Evidence rows with user_confirmed=False."""
    motion_id = await _create_motion(client, auth_headers)

    with patch(
        "app.services.gmail_evidence_service.fetch_bodies",
        return_value=MOCK_BODIES,
    ):
        resp = await client.post(
            f"/api/v1/motions/{motion_id}/gmail/import",
            json={"access_token": "ya29.tok", "message_ids": ["abc123"]},
            headers=auth_headers,
        )

    assert resp.status_code == 201
    items = resp.json()
    assert len(items) == 1
    item = items[0]
    # Must be unconfirmed — user has not reviewed it yet
    assert item["user_confirmed"] is False
    assert item["evidence_type"] == "email"
    assert item["motion_id"] == motion_id
    assert item["tags"] == []
    assert item["source_date"] == "2024-03-10"
    assert item["description"] == "Re: Custody schedule"
    # body_text stored as transcription (editable suggestion)
    assert "won't be bringing" in item["transcription"]


async def test_import_enforces_ownership(client: AsyncClient, auth_headers: dict, gmail_env):
    """Another user cannot import evidence into a motion they don't own."""
    motion_id = await _create_motion(client, auth_headers)

    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "attacker@example.com",
            "password": "attackerpass123",
            "full_name": "Attacker",
            "phone": "000-000-0002",
        },
    )
    login_resp = await client.post(
        "/api/v1/auth/token",
        data={"username": "attacker@example.com", "password": "attackerpass123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    other_headers = {"Authorization": f"Bearer {login_resp.json()['access_token']}"}

    resp = await client.post(
        f"/api/v1/motions/{motion_id}/gmail/import",
        json={"access_token": "ya29.tok", "message_ids": ["abc123"]},
        headers=other_headers,
    )
    assert resp.status_code == 404


async def test_no_token_stored_in_evidence_row(client: AsyncClient, auth_headers: dict, gmail_env):
    """Verify that neither access_token nor any OAuth token appears in Evidence fields."""
    motion_id = await _create_motion(client, auth_headers)

    with patch(
        "app.services.gmail_evidence_service.fetch_bodies",
        return_value=MOCK_BODIES,
    ):
        resp = await client.post(
            f"/api/v1/motions/{motion_id}/gmail/import",
            json={"access_token": "ya29.supersecret", "message_ids": ["abc123"]},
            headers=auth_headers,
        )

    assert resp.status_code == 201
    item = resp.json()[0]
    # None of the OAuth token should appear in any serialised Evidence field
    for field_value in item.values():
        assert "ya29.supersecret" not in str(field_value)


async def test_unauthenticated_scan_returns_401(client: AsyncClient, gmail_env):
    """Unauthenticated access to scan should return 401, not 404."""
    resp = await client.post(
        "/api/v1/motions/any-id/gmail/scan",
        json={"access_token": "tok"},
    )
    assert resp.status_code == 401


async def test_gmail_service_get_auth_url():
    """Unit-test the service function itself (no HTTP layer)."""
    with (
        patch.dict(
            os.environ,
            {
                "GMAIL_OAUTH_CLIENT_ID": "cid",
                "GMAIL_OAUTH_CLIENT_SECRET": "csec",
                "GMAIL_OAUTH_REDIRECT_URI": "http://localhost/cb",
            },
        ),
        patch("app.services.gmail_evidence_service._build_flow") as mock_flow,
    ):
        mock_flow_instance = MagicMock()
        mock_flow_instance.authorization_url.return_value = (
            "https://accounts.google.com/auth?state=x",
            "state-token",
        )
        mock_flow.return_value = mock_flow_instance

        from app.services import gmail_evidence_service
        url = gmail_evidence_service.get_auth_url()
        assert url.startswith("https://")
