"""
Storage backend failures must fail the upload loudly — never a silent
fallback to local disk, whose files evaporate on ephemeral hosting.
"""
import io
from pathlib import Path

import httpx
import pytest
from httpx import AsyncClient

from app.services import evidence_storage_service
from app.services.evidence_storage_service import EvidenceStorageError

pytestmark = pytest.mark.asyncio


async def _create_motion(client: AsyncClient, headers: dict) -> str:
    resp = await client.post(
        "/api/v1/motions/",
        json={
            "motion_type": "RFO",
            "title": "Test Motion",
            "description": "For storage failure tests",
        },
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


@pytest.fixture
def supabase_backend(monkeypatch):
    monkeypatch.setenv("STORAGE_BACKEND", "supabase")
    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setenv("SUPABASE_SERVICE_KEY", "dummy-key")


def test_save_file_raises_on_supabase_error(supabase_backend, monkeypatch, tmp_path):
    def broken_post(*args, **kwargs):
        raise httpx.ConnectError("connection refused")

    monkeypatch.setattr(httpx, "post", broken_post)
    monkeypatch.setattr(evidence_storage_service, "_UPLOADS_ROOT", tmp_path / "uploads")

    with pytest.raises(EvidenceStorageError):
        evidence_storage_service.save_file("motion-x", "note.txt", b"hello")

    # No silent local fallback
    assert not (tmp_path / "uploads").exists()


async def test_upload_returns_502_and_no_orphan_row(
    client: AsyncClient, auth_headers: dict, supabase_backend, monkeypatch
):
    def broken_post(*args, **kwargs):
        raise httpx.ConnectError("connection refused")

    monkeypatch.setattr(httpx, "post", broken_post)

    motion_id = await _create_motion(client, auth_headers)
    resp = await client.post(
        f"/api/v1/motions/{motion_id}/evidence/upload",
        data={"evidence_type": "text", "tags": '["threat"]', "description": "note"},
        files={"file": ("note.txt", io.BytesIO(b"hello"), "text/plain")},
        headers=auth_headers,
    )

    assert resp.status_code == 502
    assert "nothing was saved" in resp.json()["detail"].lower()

    listing = await client.get(
        f"/api/v1/motions/{motion_id}/evidence", headers=auth_headers
    )
    assert listing.status_code == 200
    assert listing.json() == []
