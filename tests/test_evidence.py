"""
Tests for evidence storage backend.
"""
import io
import pytest
import pytest_asyncio
from unittest.mock import MagicMock, patch
from httpx import AsyncClient


pytestmark = pytest.mark.asyncio

VALID_TAGS = ["threat", "non_payment", "custody_violation", "promise_to_follow", "false_claim", "other"]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _create_motion(client: AsyncClient, headers: dict) -> str:
    """Create a motion and return its id."""
    resp = await client.post(
        "/api/v1/motions/",
        json={
            "motion_type": "RFO",
            "title": "Test Motion",
            "description": "For evidence tests",
        },
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


async def _create_evidence(client: AsyncClient, headers: dict, motion_id: str, **overrides) -> dict:
    payload = {
        "evidence_type": "text",
        "tags": ["threat"],
        "source_date": "2024-03-15",
        "description": "Threatening message received",
        "transcription": None,
        **overrides,
    }
    resp = await client.post(
        f"/api/v1/motions/{motion_id}/evidence",
        json=payload,
        headers=headers,
    )
    return resp


# ---------------------------------------------------------------------------
# CRUD happy paths
# ---------------------------------------------------------------------------

async def test_create_evidence_returns_201(client: AsyncClient, auth_headers: dict):
    motion_id = await _create_motion(client, auth_headers)
    resp = await _create_evidence(client, auth_headers, motion_id)
    assert resp.status_code == 201
    data = resp.json()
    assert data["motion_id"] == motion_id
    assert data["evidence_type"] == "text"
    assert data["tags"] == ["threat"]
    assert data["source_date"] == "2024-03-15"
    assert data["user_confirmed"] is False


async def test_create_evidence_null_source_date(client: AsyncClient, auth_headers: dict):
    motion_id = await _create_motion(client, auth_headers)
    resp = await _create_evidence(client, auth_headers, motion_id, source_date=None)
    assert resp.status_code == 201
    assert resp.json()["source_date"] is None


async def test_list_evidence(client: AsyncClient, auth_headers: dict):
    motion_id = await _create_motion(client, auth_headers)
    await _create_evidence(client, auth_headers, motion_id)
    await _create_evidence(client, auth_headers, motion_id, tags=["non_payment"])

    resp = await client.get(
        f"/api/v1/motions/{motion_id}/evidence",
        headers=auth_headers,
    )
    assert resp.status_code == 200
    items = resp.json()
    assert len(items) == 2


async def test_update_evidence(client: AsyncClient, auth_headers: dict):
    motion_id = await _create_motion(client, auth_headers)
    create_resp = await _create_evidence(client, auth_headers, motion_id)
    evidence_id = create_resp.json()["id"]

    resp = await client.put(
        f"/api/v1/evidence/{evidence_id}",
        json={"tags": ["false_claim"], "user_confirmed": True},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["tags"] == ["false_claim"]
    assert data["user_confirmed"] is True


async def test_delete_evidence(client: AsyncClient, auth_headers: dict):
    motion_id = await _create_motion(client, auth_headers)
    create_resp = await _create_evidence(client, auth_headers, motion_id)
    evidence_id = create_resp.json()["id"]

    del_resp = await client.delete(
        f"/api/v1/evidence/{evidence_id}",
        headers=auth_headers,
    )
    assert del_resp.status_code == 204

    list_resp = await client.get(
        f"/api/v1/motions/{motion_id}/evidence",
        headers=auth_headers,
    )
    assert list_resp.json() == []


# ---------------------------------------------------------------------------
# Ownership enforcement
# ---------------------------------------------------------------------------

async def test_other_user_cannot_list_evidence(client: AsyncClient, auth_headers: dict):
    """A second user cannot list evidence belonging to another user's motion."""
    motion_id = await _create_motion(client, auth_headers)
    await _create_evidence(client, auth_headers, motion_id)

    # Register and log in as a different user
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "other@example.com",
            "password": "otherpass123",
            "full_name": "Other User",
            "phone": "111-222-3333",
        },
    )
    login_resp = await client.post(
        "/api/v1/auth/token",
        data={"username": "other@example.com", "password": "otherpass123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    other_headers = {"Authorization": f"Bearer {login_resp.json()['access_token']}"}

    resp = await client.get(
        f"/api/v1/motions/{motion_id}/evidence",
        headers=other_headers,
    )
    assert resp.status_code == 404


async def test_other_user_cannot_delete_evidence(client: AsyncClient, auth_headers: dict):
    motion_id = await _create_motion(client, auth_headers)
    create_resp = await _create_evidence(client, auth_headers, motion_id)
    evidence_id = create_resp.json()["id"]

    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "thief@example.com",
            "password": "thiefpass123",
            "full_name": "Thief User",
            "phone": "999-888-7777",
        },
    )
    login_resp = await client.post(
        "/api/v1/auth/token",
        data={"username": "thief@example.com", "password": "thiefpass123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    other_headers = {"Authorization": f"Bearer {login_resp.json()['access_token']}"}

    resp = await client.delete(
        f"/api/v1/evidence/{evidence_id}",
        headers=other_headers,
    )
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Tag validation
# ---------------------------------------------------------------------------

async def test_invalid_tag_returns_400(client: AsyncClient, auth_headers: dict):
    motion_id = await _create_motion(client, auth_headers)
    resp = await _create_evidence(client, auth_headers, motion_id, tags=["invalid_tag"])
    assert resp.status_code == 400


async def test_all_valid_tags_accepted(client: AsyncClient, auth_headers: dict):
    motion_id = await _create_motion(client, auth_headers)
    resp = await _create_evidence(client, auth_headers, motion_id, tags=VALID_TAGS)
    assert resp.status_code == 201


async def test_update_with_invalid_tag_returns_400(client: AsyncClient, auth_headers: dict):
    motion_id = await _create_motion(client, auth_headers)
    create_resp = await _create_evidence(client, auth_headers, motion_id)
    evidence_id = create_resp.json()["id"]

    resp = await client.put(
        f"/api/v1/evidence/{evidence_id}",
        json={"tags": ["bogus"]},
        headers=auth_headers,
    )
    assert resp.status_code == 400


# ---------------------------------------------------------------------------
# File upload
# ---------------------------------------------------------------------------

async def test_upload_text_file(client: AsyncClient, auth_headers: dict):
    motion_id = await _create_motion(client, auth_headers)
    file_content = b"This is a text evidence file."
    resp = await client.post(
        f"/api/v1/motions/{motion_id}/evidence/upload",
        files={"file": ("evidence.txt", io.BytesIO(file_content), "text/plain")},
        data={"evidence_type": "document", "tags": '["other"]', "description": "A text file"},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["filename"] == "evidence.txt"
    assert data["storage_path"] is not None


async def test_upload_image_file(client: AsyncClient, auth_headers: dict):
    motion_id = await _create_motion(client, auth_headers)
    # Minimal valid PNG bytes (1x1 pixel)
    png_bytes = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00"
        b"\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    resp = await client.post(
        f"/api/v1/motions/{motion_id}/evidence/upload",
        files={"file": ("screenshot.png", io.BytesIO(png_bytes), "image/png")},
        data={"evidence_type": "photo", "tags": '["threat"]', "description": "Screenshot"},
        headers=auth_headers,
    )
    assert resp.status_code == 201


async def test_upload_disallowed_file_type_returns_400(client: AsyncClient, auth_headers: dict):
    motion_id = await _create_motion(client, auth_headers)
    resp = await client.post(
        f"/api/v1/motions/{motion_id}/evidence/upload",
        files={"file": ("malware.exe", io.BytesIO(b"MZ\x90"), "application/octet-stream")},
        data={"evidence_type": "document", "tags": '["other"]', "description": "Bad file"},
        headers=auth_headers,
    )
    assert resp.status_code == 400


async def test_upload_file_too_large_returns_413(client: AsyncClient, auth_headers: dict):
    motion_id = await _create_motion(client, auth_headers)
    # 11 MB — exceeds 10 MB limit
    big_content = b"x" * (11 * 1024 * 1024)
    resp = await client.post(
        f"/api/v1/motions/{motion_id}/evidence/upload",
        files={"file": ("big.pdf", io.BytesIO(big_content), "application/pdf")},
        data={"evidence_type": "document", "tags": '["other"]', "description": "Too big"},
        headers=auth_headers,
    )
    assert resp.status_code == 413


# ---------------------------------------------------------------------------
# File sanitization
# ---------------------------------------------------------------------------

async def test_filename_sanitized(client: AsyncClient, auth_headers: dict):
    motion_id = await _create_motion(client, auth_headers)
    resp = await client.post(
        f"/api/v1/motions/{motion_id}/evidence/upload",
        files={"file": ("../../etc/passwd.txt", io.BytesIO(b"root:x:0:0"), "text/plain")},
        data={"evidence_type": "document", "tags": '["other"]', "description": "Path traversal attempt"},
        headers=auth_headers,
    )
    # Should succeed but with sanitized filename
    assert resp.status_code == 201
    data = resp.json()
    assert ".." not in data["filename"]
    assert "/" not in data["filename"]


async def test_empty_filename_rejected(client: AsyncClient, auth_headers: dict):
    motion_id = await _create_motion(client, auth_headers)
    resp = await client.post(
        f"/api/v1/motions/{motion_id}/evidence/upload",
        files={"file": ("", io.BytesIO(b"data"), "text/plain")},
        data={"evidence_type": "document", "tags": '["other"]', "description": "No filename"},
        headers=auth_headers,
    )
    # 400 or 422 — both indicate a rejected request; exact code depends on framework validation layer
    assert resp.status_code in (400, 422)


# ---------------------------------------------------------------------------
# Auth required
# ---------------------------------------------------------------------------

async def test_unauthenticated_returns_401(client: AsyncClient):
    resp = await client.get("/api/v1/motions/nonexistent/evidence")
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# OCR suggestion on image upload (env-gated)
# ---------------------------------------------------------------------------

PNG_BYTES = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00"
    b"\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
)


async def test_ocr_suggestion_included_in_upload_response_when_flag_on(
    client: AsyncClient, auth_headers: dict, monkeypatch
):
    """With OCR on + mocked vision, image upload response includes suggested_transcription."""
    monkeypatch.setenv("OCR_ENABLED", "true")

    from app.services import ocr_service

    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.full_text_annotation.text = "Mocked OCR text"
    mock_client.document_text_detection.return_value = mock_response

    motion_id = await _create_motion(client, auth_headers)

    with patch.object(ocr_service, "_VISION_AVAILABLE", True):
        with patch.object(ocr_service, "_build_vision_client", return_value=mock_client):
            resp = await client.post(
                f"/api/v1/motions/{motion_id}/evidence/upload",
                files={"file": ("screenshot.png", io.BytesIO(PNG_BYTES), "image/png")},
                data={"evidence_type": "photo", "tags": '["threat"]', "description": "Screenshot"},
                headers=auth_headers,
            )

    assert resp.status_code == 201
    data = resp.json()
    assert data.get("suggested_transcription") == "Mocked OCR text"
    # Stored transcription must NOT be auto-set; user_confirmed must remain False
    assert data["transcription"] is None
    assert data["user_confirmed"] is False


async def test_ocr_stored_transcription_not_set_user_confirmed_false(
    client: AsyncClient, auth_headers: dict, monkeypatch
):
    """OCR suggestion never sets stored transcription or user_confirmed=True."""
    monkeypatch.setenv("OCR_ENABLED", "true")

    from app.services import ocr_service

    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.full_text_annotation.text = "Some extracted text"
    mock_client.document_text_detection.return_value = mock_response

    motion_id = await _create_motion(client, auth_headers)

    with patch.object(ocr_service, "_VISION_AVAILABLE", True):
        with patch.object(ocr_service, "_build_vision_client", return_value=mock_client):
            resp = await client.post(
                f"/api/v1/motions/{motion_id}/evidence/upload",
                files={"file": ("photo.jpg", io.BytesIO(PNG_BYTES), "image/jpeg")},
                data={"evidence_type": "photo", "tags": '["other"]', "description": "Photo"},
                headers=auth_headers,
            )

    assert resp.status_code == 201
    data = resp.json()
    assert data["transcription"] is None
    assert data["user_confirmed"] is False


async def test_no_ocr_suggestion_when_flag_off(
    client: AsyncClient, auth_headers: dict, monkeypatch
):
    """With OCR flag off, image upload response has no suggested_transcription key (or null)."""
    monkeypatch.delenv("OCR_ENABLED", raising=False)

    motion_id = await _create_motion(client, auth_headers)
    resp = await client.post(
        f"/api/v1/motions/{motion_id}/evidence/upload",
        files={"file": ("screenshot.png", io.BytesIO(PNG_BYTES), "image/png")},
        data={"evidence_type": "photo", "tags": '["threat"]', "description": "Screenshot"},
        headers=auth_headers,
    )

    assert resp.status_code == 201
    data = resp.json()
    # suggested_transcription must be absent or null when OCR is off
    assert data.get("suggested_transcription") is None


async def test_no_ocr_suggestion_for_non_image_file(
    client: AsyncClient, auth_headers: dict, monkeypatch
):
    """OCR is not attempted for non-image uploads (e.g. PDF); no suggested_transcription."""
    monkeypatch.setenv("OCR_ENABLED", "true")

    from app.services import ocr_service

    mock_client = MagicMock()

    motion_id = await _create_motion(client, auth_headers)

    with patch.object(ocr_service, "_VISION_AVAILABLE", True):
        with patch.object(ocr_service, "_build_vision_client", return_value=mock_client):
            resp = await client.post(
                f"/api/v1/motions/{motion_id}/evidence/upload",
                files={"file": ("document.pdf", io.BytesIO(b"%PDF-1.4"), "application/pdf")},
                data={"evidence_type": "document", "tags": '["other"]', "description": "PDF"},
                headers=auth_headers,
            )

    assert resp.status_code == 201
    data = resp.json()
    assert data.get("suggested_transcription") is None
    # Vision client must NOT have been called for a PDF
    mock_client.document_text_detection.assert_not_called()
