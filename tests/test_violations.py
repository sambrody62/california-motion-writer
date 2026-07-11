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


async def test_motion_detail_returns_violation_declaration(
    client: AsyncClient, auth_headers: dict
):
    """Regression for the 2026-07-11 real-LLM finding L14: violations store the
    declaration on generated_text with no drafts, but motion detail omitted it,
    so the preview page had nothing to review before filing."""
    await _create_profile(client, auth_headers)
    resp = await client.post(
        "/api/v1/violations/process", json=_intake(), headers=auth_headers
    )
    assert resp.status_code == 200, resp.text
    declaration = resp.json()["declaration"]

    listing = await client.get("/api/v1/motions/", headers=auth_headers)
    motion_id = [m for m in listing.json() if m["motion_type"] == "VIOLATION"][0]["id"]

    detail = await client.get(f"/api/v1/motions/{motion_id}", headers=auth_headers)
    assert detail.status_code == 200, detail.text
    body = detail.json()
    assert body["generated_text"] == declaration
    assert body["drafts"] == []


async def test_motion_detail_keeps_generated_text_null_for_rfo(
    client: AsyncClient, auth_headers: dict
):
    resp = await client.post(
        "/api/v1/motions/",
        json={"motion_type": "RFO", "title": "Custody RFO"},
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.text
    motion_id = resp.json()["id"]

    detail = await client.get(f"/api/v1/motions/{motion_id}", headers=auth_headers)
    assert detail.status_code == 200, detail.text
    assert detail.json()["generated_text"] is None


async def test_invalid_payload_is_4xx_not_500(client: AsyncClient, auth_headers: dict):
    resp = await client.post(
        "/api/v1/violations/process",
        json={"violationType": "Visitation"},  # missing required fields
        headers=auth_headers,
    )
    assert 400 <= resp.status_code < 500


# ---------------------------------------------------------------------------
# /violations/intake-questions must serve the wizard-step shape the frontend
# renders. Regression for the 2026-07-11 real-LLM browser finding L5: the
# endpoint returned the flat form-config map and #/violation/intake crashed
# to a blank screen for every user.
# ---------------------------------------------------------------------------


async def _get_intake_steps(client: AsyncClient, headers: dict) -> dict:
    resp = await client.get("/api/v1/violations/intake-questions", headers=headers)
    assert resp.status_code == 200, resp.text
    return resp.json()["questions"]


async def test_intake_questions_are_three_wizard_steps(
    client: AsyncClient, auth_headers: dict
):
    steps = await _get_intake_steps(client, auth_headers)

    numbers = []
    for step in steps.values():
        assert {"step_number", "step_name", "description", "questions"} <= set(step)
        assert step["step_name"].strip()
        assert step["description"].strip()
        assert isinstance(step["questions"], list) and step["questions"]
        numbers.append(step["step_number"])
    assert sorted(numbers) == [1, 2, 3]


async def test_intake_question_ids_match_process_contract(
    client: AsyncClient, auth_headers: dict
):
    """Every wizard answer must land on a ViolationIntakeRequest field, and
    every field must be collectable — otherwise sworn input is silently lost."""
    from app.api.v1.endpoints.violations import ViolationIntakeRequest

    steps = await _get_intake_steps(client, auth_headers)
    ids = [q["id"] for step in steps.values() for q in step["questions"]]

    assert len(ids) == len(set(ids))
    assert set(ids) == set(ViolationIntakeRequest.model_fields)


async def test_intake_questions_are_renderable(
    client: AsyncClient, auth_headers: dict
):
    """Types must be ones ViolationQuestionField.tsx can render, with the
    config's own options on the multi-selects and Yes/No on booleans."""
    from app.api.v1.endpoints.violations import violation_service

    config = violation_service.config["violationFiling"]["intakeQuestions"]
    steps = await _get_intake_steps(client, auth_headers)
    questions = {q["id"]: q for step in steps.values() for q in step["questions"]}

    for q in questions.values():
        assert q["type"] in {"text", "textarea", "select", "radio", "checkbox", "date"}
        assert q["label"].strip()

    assert questions["urgency"]["type"] == "radio"
    assert questions["urgency"]["options"] == ["Yes", "No"]
    assert questions["evidence"]["type"] == "checkbox"
    assert questions["evidence"]["options"] == config["evidence"]["options"]
    assert questions["requestedRelief"]["type"] == "checkbox"
    assert questions["requestedRelief"]["options"] == config["requestedRelief"]["options"]
