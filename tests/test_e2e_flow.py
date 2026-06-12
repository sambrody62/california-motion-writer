"""
End-to-end flow test: register → profile → RFO motion → drafts → LLM → PDF.
Runs entirely with the mock LLM (USE_MOCK_LLM=true set in conftest.py).
"""
import pytest
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_full_rfo_journey(client: AsyncClient):
    """
    Full happy-path journey in mock-LLM mode:
      1. Register a user (201)
      2. Create a profile (201)
      3. Create an RFO motion (201)
      4. Save 2 draft steps
      5. POST /llm/process-motion
      6. GET /motions/{id} → drafts have llm_output populated
      7. POST /documents/generate-pdf-sync → PDF bytes > 10 KB containing party name
    """
    # ------------------------------------------------------------------
    # 1. Register user
    # ------------------------------------------------------------------
    register_resp = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "e2e_user@example.com",
            "password": "e2epassword1",
            "full_name": "E2E Test User",
            "phone": "555-000-1111",
        },
    )
    assert register_resp.status_code == 201, register_resp.text
    token = register_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # ------------------------------------------------------------------
    # 2. Create profile
    # ------------------------------------------------------------------
    profile_resp = await client.post(
        "/api/v1/profiles",
        json={
            "case_number": "FL-2025-E2E",
            "county": "Los Angeles",
            "court_branch": "Stanley Mosk Courthouse",
            "department": "Dept. 42",
            "is_petitioner": True,
            "party_name": "Alice Petitioner",
            "party_address": "100 Main St, Los Angeles, CA 90001",
            "party_phone": "555-100-2000",
            "other_party_name": "Bob Respondent",
            "other_party_address": "200 Oak Ave, Los Angeles, CA 90002",
            "children_info": [
                {"name": "Child One", "birthdate": "2018-03-15", "ssn_last_4": "9999"}
            ],
        },
        headers=headers,
    )
    assert profile_resp.status_code == 201, profile_resp.text

    # ------------------------------------------------------------------
    # 3. Create RFO motion
    # ------------------------------------------------------------------
    motion_resp = await client.post(
        "/api/v1/motions",
        json={
            "motion_type": "RFO",
            "title": "E2E Request for Order — Custody",
            "description": "E2E test motion for custody modification",
            "case_caption": "Alice Petitioner v. Bob Respondent",
            "filing_track": "standard",
            "courthouse": "Los Angeles Superior Court",
            "intake_data": {"reason": "Change in circumstances"},
        },
        headers=headers,
    )
    assert motion_resp.status_code == 201, motion_resp.text
    motion_id = motion_resp.json()["id"]

    # ------------------------------------------------------------------
    # 4. Save 2 draft steps
    # ------------------------------------------------------------------
    draft1_resp = await client.post(
        f"/api/v1/motions/{motion_id}/drafts",
        json={
            "step_number": 1,
            "step_name": "relief_requested",
            "question_data": {
                "relief": "sole legal and physical custody",
                "reason": "Child's welfare requires stability",
            },
        },
        headers=headers,
    )
    assert draft1_resp.status_code in (200, 201), draft1_resp.text

    draft2_resp = await client.post(
        f"/api/v1/motions/{motion_id}/drafts",
        json={
            "step_number": 2,
            "step_name": "facts_and_circumstances",
            "question_data": {
                "changed_circumstances": "Other parent relocated 50 miles away",
                "impact_on_child": "Disrupts school and medical routines",
            },
        },
        headers=headers,
    )
    assert draft2_resp.status_code in (200, 201), draft2_resp.text

    # ------------------------------------------------------------------
    # 5. POST /llm/process-motion
    # ------------------------------------------------------------------
    llm_resp = await client.post(
        "/api/v1/llm/process-motion",
        json={"motion_id": motion_id},
        headers=headers,
    )
    assert llm_resp.status_code == 200, llm_resp.text
    llm_data = llm_resp.json()
    assert llm_data["success"] is True
    assert llm_data["sections_processed"] == 2

    # ------------------------------------------------------------------
    # 6. GET /motions/{id} → drafts have llm_output populated
    # ------------------------------------------------------------------
    get_resp = await client.get(f"/api/v1/motions/{motion_id}", headers=headers)
    assert get_resp.status_code == 200, get_resp.text
    motion_detail = get_resp.json()
    drafts = motion_detail["drafts"]
    assert len(drafts) == 2
    for draft in drafts:
        assert draft["llm_output"] is not None, (
            f"Draft step {draft['step_number']} missing llm_output"
        )
        assert len(draft["llm_output"]) > 0

    # ------------------------------------------------------------------
    # 7. POST /documents/generate-pdf-sync → PDF bytes > 10 KB
    #    containing the party name "Alice Petitioner"
    # ------------------------------------------------------------------
    pdf_resp = await client.post(
        "/api/v1/documents/generate-pdf-sync",
        json={"motion_id": motion_id},
        headers=headers,
    )
    assert pdf_resp.status_code == 200, pdf_resp.text
    assert pdf_resp.headers["content-type"] == "application/pdf"

    pdf_bytes = pdf_resp.content
    assert len(pdf_bytes) > 10_000, (
        f"PDF too small: {len(pdf_bytes)} bytes (expected > 10 KB)"
    )
    # PDF streams encode spaces as \040 (octal), so search for both encodings.
    party_name_present = (
        b"Alice Petitioner" in pdf_bytes
        or b"Alice\\040Petitioner" in pdf_bytes
        or (b"Alice" in pdf_bytes and b"Petitioner" in pdf_bytes)
    )
    assert party_name_present, (
        "Party name 'Alice Petitioner' not found in PDF bytes"
    )

    # Expose byte count via a module-level variable so the caller can read it
    test_full_rfo_journey.pdf_bytes = len(pdf_bytes)
