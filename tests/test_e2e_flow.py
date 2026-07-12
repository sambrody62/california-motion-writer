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


@pytest.mark.asyncio
async def test_full_rfo_journey_with_evidence(client: AsyncClient):
    """
    Full happy-path journey in mock-LLM mode with evidence:
      1. Register a user (201)
      2. Create a profile (201)
      3. Create an RFO motion (201)
      4. Save 2 draft steps
      5. POST /llm/process-motion
      6. Create 2 confirmed tagged evidence items via the API
      7. POST /documents/generate-pdf-sync (no evidence) → baseline size
      8. POST /documents/generate-pdf-sync (with confirmed evidence) → assert
         - PDF contains 'EXHIBIT A'
         - PDF is larger than the no-evidence packet
    """
    # ------------------------------------------------------------------
    # 1. Register user
    # ------------------------------------------------------------------
    register_resp = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "e2e_evidence@example.com",
            "password": "e2epassword1",
            "full_name": "Evidence Test User",
            "phone": "555-000-2222",
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
            "case_number": "FL-2025-EV01",
            "county": "Los Angeles",
            "court_branch": "Stanley Mosk Courthouse",
            "department": "Dept. 10",
            "is_petitioner": True,
            "party_name": "Carol Petitioner",
            "party_address": "300 Elm St, Los Angeles, CA 90005",
            "party_phone": "555-300-4000",
            "other_party_name": "Dave Respondent",
            "other_party_address": "400 Pine Ave, Los Angeles, CA 90006",
            "children_info": [
                {"name": "Child Two", "birthdate": "2016-07-20", "ssn_last_4": "1111"}
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
            "title": "E2E Evidence — Custody",
            "description": "E2E test motion with evidence",
            "case_caption": "Carol Petitioner v. Dave Respondent",
            "filing_track": "standard",
            "courthouse": "Los Angeles Superior Court",
            "intake_data": {"reason": "Evidence-backed custody change"},
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
                "changed_circumstances": "Documented violations of custody order",
                "impact_on_child": "Child's routine disrupted by missed exchanges",
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
    assert llm_resp.json()["success"] is True

    # ------------------------------------------------------------------
    # 6. Create 2 confirmed tagged evidence items
    # ------------------------------------------------------------------
    ev1_resp = await client.post(
        f"/api/v1/motions/{motion_id}/evidence",
        json={
            "evidence_type": "text",
            "tags": ["custody_violation"],
            "source_date": "2025-01-10",
            "description": "Respondent failed to exchange child on agreed date",
            "transcription": "I am not bringing the child today.",
        },
        headers=headers,
    )
    assert ev1_resp.status_code == 201, ev1_resp.text
    ev1_id = ev1_resp.json()["id"]

    ev2_resp = await client.post(
        f"/api/v1/motions/{motion_id}/evidence",
        json={
            "evidence_type": "text",
            "tags": ["threat"],
            "source_date": "2025-02-14",
            "description": "Threatening text message received from respondent",
            "transcription": "You will regret taking me to court.",
        },
        headers=headers,
    )
    assert ev2_resp.status_code == 201, ev2_resp.text
    ev2_id = ev2_resp.json()["id"]

    # Confirm both evidence items
    for ev_id in (ev1_id, ev2_id):
        confirm_resp = await client.put(
            f"/api/v1/evidence/{ev_id}",
            json={"user_confirmed": True},
            headers=headers,
        )
        assert confirm_resp.status_code == 200, confirm_resp.text
        assert confirm_resp.json()["user_confirmed"] is True

    # ------------------------------------------------------------------
    # 7. Baseline: generate PDF without evidence (different motion user, but
    #    we need a clean baseline — we'll use a separate motion for no-evidence)
    #    Simpler: generate two PDFs from the *same* motion:
    #      a) First delete the evidence temporarily — not possible via API, so
    #         instead we create a second motion (no evidence) in the same
    #         profile to get a baseline size.
    # ------------------------------------------------------------------
    motion_bare_resp = await client.post(
        "/api/v1/motions",
        json={
            "motion_type": "RFO",
            "title": "Bare motion for baseline",
            "description": "No evidence attached",
            "case_caption": "Carol Petitioner v. Dave Respondent",
            "filing_track": "standard",
            "courthouse": "Los Angeles Superior Court",
            "intake_data": {},
        },
        headers=headers,
    )
    assert motion_bare_resp.status_code == 201, motion_bare_resp.text
    bare_motion_id = motion_bare_resp.json()["id"]

    bare_draft_resp = await client.post(
        f"/api/v1/motions/{bare_motion_id}/drafts",
        json={
            "step_number": 1,
            "step_name": "facts",
            "question_data": {"facts": "baseline motion with no evidence"},
        },
        headers=headers,
    )
    assert bare_draft_resp.status_code in (200, 201), bare_draft_resp.text

    bare_llm_resp = await client.post(
        "/api/v1/llm/process-motion",
        json={"motion_id": bare_motion_id},
        headers=headers,
    )
    assert bare_llm_resp.status_code == 200, bare_llm_resp.text

    pdf_bare_resp = await client.post(
        "/api/v1/documents/generate-pdf-sync",
        json={"motion_id": bare_motion_id},
        headers=headers,
    )
    assert pdf_bare_resp.status_code == 200, pdf_bare_resp.text
    pdf_bare_bytes = pdf_bare_resp.content

    # ------------------------------------------------------------------
    # 8. Generate PDF with confirmed evidence
    # ------------------------------------------------------------------
    pdf_ev_resp = await client.post(
        "/api/v1/documents/generate-pdf-sync",
        json={"motion_id": motion_id},
        headers=headers,
    )
    assert pdf_ev_resp.status_code == 200, pdf_ev_resp.text
    assert pdf_ev_resp.headers["content-type"] == "application/pdf"

    pdf_ev_bytes = pdf_ev_resp.content

    # Assert 'EXHIBIT A' is present in the evidence PDF
    import io as _io
    import PyPDF2 as _PyPDF2
    reader = _PyPDF2.PdfReader(_io.BytesIO(pdf_ev_bytes))
    full_text = "".join(page.extract_text() or "" for page in reader.pages)
    assert "EXHIBIT A" in full_text, (
        f"'EXHIBIT A' not found in evidence PDF text. PDF size: {len(pdf_ev_bytes)} bytes"
    )

    # Assert evidence PDF is larger than no-evidence baseline
    assert len(pdf_ev_bytes) > len(pdf_bare_bytes), (
        f"Evidence PDF ({len(pdf_ev_bytes)} bytes) must be larger than "
        f"bare PDF ({len(pdf_bare_bytes)} bytes)"
    )
