"""
Generated violation declarations must pass through the fact gate before they
are stored or returned (split from test_violations.py for the 300-line limit).

Fixtures are the verbatim Flow-4 sworn-statement embellishments from the
2026-07-11 real-LLM browser report (findings L4, L7, L15).
"""
import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock

# Patch via the endpoint module's binding (another suite file reloads
# app.services.llm_service, so module attributes can diverge from it)
from app.api.v1.endpoints import violations as violations_endpoint

pytestmark = pytest.mark.asyncio

FABRICATED_DECLARATION = (
    "I, [PETITIONER'S FULL LEGAL NAME], declare as follows.\n\n"
    "Throughout the weekend of June 20-22, 2026, Respondent's cellular "
    "telephone was turned off or otherwise unavailable.\n\n"
    "I attempted to reach Respondent by telephone on multiple occasions.\n\n"
    "I respectfully request that the court issue monetary sanctions against "
    "Respondent pursuant to Family Code section 3027.1."
)


def _intake() -> dict:
    return {
        "violationType": "Visitation",
        "urgency": False,
        "violationDates": ["2026-06-20"],
        "violationDescription": "Respondent denied the scheduled weekend visit.",
        "evidence": ["Text messages"],
        "attemptedResolution": False,
        "priorViolations": False,
        "requestedRelief": ["Order compliance"],
    }


async def _create_profile(client: AsyncClient, headers: dict) -> None:
    resp = await client.post(
        "/api/v1/profiles/",
        json={
            "case_number": "23FL009876S",
            "county": "San Diego",
            "is_petitioner": True,
            "party_name": "Rosa Martinez",
            "other_party_name": "Miguel Martinez",
        },
        headers=headers,
    )
    assert resp.status_code == 201, resp.text


def _mock_enhance(monkeypatch) -> None:
    monkeypatch.setattr(
        violations_endpoint.violation_service.llm_service,
        "enhance_declaration",
        AsyncMock(return_value={
            "success": True,
            "enhanced_text": FABRICATED_DECLARATION,
            "tokens_used": 10,
        }),
    )


async def test_process_gates_declaration_and_stores_report(
    client: AsyncClient, auth_headers: dict, monkeypatch
):
    await _create_profile(client, auth_headers)
    _mock_enhance(monkeypatch)

    resp = await client.post(
        "/api/v1/violations/process", json=_intake(), headers=auth_headers
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    declaration = body["declaration"]

    # L15: placeholder filled from the profile the endpoint now passes through
    assert "[PETITIONER'S FULL LEGAL NAME]" not in declaration
    assert "Rosa Martinez" in declaration
    # L4: the un-entered June 22 is trimmed to the date the user gave
    assert "June 20-22, 2026" not in declaration
    assert "June 20, 2026" in declaration
    # L7: invented statute stripped
    assert "3027.1" not in declaration
    # Quantifier embellishment flagged but never edited
    assert "multiple occasions" in declaration

    types = {c["type"] for c in body["corrections"]}
    assert {"placeholder_filled", "date", "authority_removed", "quantifier_flag"} <= types

    listing = await client.get("/api/v1/motions/", headers=auth_headers)
    motion_id = [m for m in listing.json() if m["motion_type"] == "VIOLATION"][0]["id"]
    detail = await client.get(f"/api/v1/motions/{motion_id}", headers=auth_headers)
    assert detail.status_code == 200, detail.text
    assert detail.json()["generated_text"] == declaration
    fact_check = detail.json()["fact_check"]
    assert fact_check["version"] == 1
    assert fact_check["corrections"] == body["corrections"]


async def test_generate_declaration_returns_gated_text_and_corrections(
    client: AsyncClient, auth_headers: dict, monkeypatch
):
    _mock_enhance(monkeypatch)

    resp = await client.post(
        "/api/v1/violations/generate-declaration",
        json=_intake(),
        headers=auth_headers,
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert "3027.1" not in body["declaration"]
    assert "June 20, 2026" in body["declaration"]
    assert "multiple occasions" in body["declaration"]
    types = {c["type"] for c in body["corrections"]}
    assert {"date", "authority_removed", "quantifier_flag"} <= types


SEMANTIC_FLAG = {
    "type": "semantic_flag",
    "severity": "needs_review",
    "section": "reviewer",
    "original": "multiple occasions",
    "replacement": None,
    "message": (
        "Our automated reviewer flagged: The intake data does not say how many "
        'attempts were made. — verify "multiple occasions" against your '
        "records before filing."
    ),
}


async def test_process_appends_semantic_flags_to_report(
    client: AsyncClient, auth_headers: dict, monkeypatch
):
    await _create_profile(client, auth_headers)
    _mock_enhance(monkeypatch)
    check_text = AsyncMock(return_value=[dict(SEMANTIC_FLAG)])
    monkeypatch.setattr(
        violations_endpoint.semantic_check_service, "check_text", check_text
    )

    resp = await client.post(
        "/api/v1/violations/process", json=_intake(), headers=auth_headers
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()

    # Reviewer flag appended after the gate's own corrections
    assert body["corrections"][-1] == SEMANTIC_FLAG
    assert {c["type"] for c in body["corrections"]} >= {
        "authority_removed",
        "semantic_flag",
    }

    # Reviewer sees the gated declaration, the raw intake, and the profile
    check_text.assert_awaited_once()
    args = check_text.await_args.args
    assert args[0] == body["declaration"]
    assert args[1]["violationType"] == "Visitation"
    assert args[2]["party_name"] == "Rosa Martinez"

    listing = await client.get("/api/v1/motions/", headers=auth_headers)
    motion_id = [m for m in listing.json() if m["motion_type"] == "VIOLATION"][0]["id"]
    detail = await client.get(f"/api/v1/motions/{motion_id}", headers=auth_headers)
    assert detail.json()["fact_check"]["corrections"] == body["corrections"]
