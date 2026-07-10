"""
/violations/process must work end-to-end through a real async session.

Regression for the 2026-07-10 user-story finding F1: the endpoint lazy-loaded
current_user.profile in an async context (MissingGreenlet) and 500'd for every
user, with the raw SQLAlchemy error leaked to the client.
"""
import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


def _intake(**overrides) -> dict:
    payload = {
        "violationType": "Visitation",
        "urgency": False,
        "violationDates": ["2026-06-06"],
        "violationDescription": "Missed three scheduled Saturday exchanges without notice.",
        "evidence": ["Text messages"],
        "attemptedResolution": False,
        "priorViolations": False,
        "requestedRelief": ["Order compliance"],
    }
    payload.update(overrides)
    return payload


async def _create_profile(client: AsyncClient, headers: dict) -> None:
    resp = await client.post(
        "/api/v1/profiles/",
        json={
            "case_number": "23FL009876S",
            "county": "San Diego",
            "party_name": "Rosa Martinez",
            "other_party_name": "Miguel Martinez",
        },
        headers=headers,
    )
    assert resp.status_code == 201, resp.text


async def test_process_with_profile_saves_violation_motion(
    client: AsyncClient, auth_headers: dict
):
    await _create_profile(client, auth_headers)

    resp = await client.post(
        "/api/v1/violations/process", json=_intake(), headers=auth_headers
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["success"] is True
    assert body["track"] == "regular"
    assert body["forms"]
    assert len(body["declaration"]) > 50

    listing = await client.get("/api/v1/motions/", headers=auth_headers)
    violations = [m for m in listing.json() if m["motion_type"] == "VIOLATION"]
    assert len(violations) == 1
    assert violations[0]["filing_track"] == "regular"


async def test_process_without_profile_succeeds(client: AsyncClient, auth_headers: dict):
    resp = await client.post(
        "/api/v1/violations/process", json=_intake(), headers=auth_headers
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["success"] is True


@pytest.mark.parametrize(
    "overrides,expected_track",
    [
        ({"urgency": True, "violationType": "Custody"}, "emergency"),
        ({"violationType": "Restraining Order"}, "emergency"),
        ({"requestedRelief": ["Find party in contempt"]}, "contempt"),
        ({}, "regular"),
    ],
)
async def test_track_determination(
    client: AsyncClient, auth_headers: dict, overrides: dict, expected_track: str
):
    resp = await client.post(
        "/api/v1/violations/process", json=_intake(**overrides), headers=auth_headers
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["track"] == expected_track


async def test_violation_motion_generates_pdf(client: AsyncClient, auth_headers: dict):
    """Violation motions have no drafts — the declaration lives on generated_text."""
    await _create_profile(client, auth_headers)
    resp = await client.post(
        "/api/v1/violations/process", json=_intake(), headers=auth_headers
    )
    assert resp.status_code == 200, resp.text

    listing = await client.get("/api/v1/motions/", headers=auth_headers)
    motion_id = [m for m in listing.json() if m["motion_type"] == "VIOLATION"][0]["id"]

    pdf = await client.post(
        "/api/v1/documents/generate-pdf-sync",
        json={"motion_id": motion_id},
        headers=auth_headers,
    )
    assert pdf.status_code == 200, pdf.text
    assert pdf.content[:4] == b"%PDF"


async def test_invalid_payload_is_4xx_not_500(client: AsyncClient, auth_headers: dict):
    resp = await client.post(
        "/api/v1/violations/process",
        json={"violationType": "Visitation"},  # missing required fields
        headers=auth_headers,
    )
    assert 400 <= resp.status_code < 500
