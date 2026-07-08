"""
Regression tests for bugs found in the 2026-07-06 live E2E run
(tasks/e2e-test-findings.md).
"""
import importlib
import os
import pytest
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient

from app.main import app


def _route_paths():
    return {route.path for route in app.routes}


class TestFrontendRouteContract:
    """Backend routes must match the paths the frontend calls (services/api.ts)."""

    def test_violations_routes_match_frontend(self):
        paths = _route_paths()
        assert "/api/v1/violations/tracks" in paths
        assert "/api/v1/violations/intake-questions" in paths
        assert "/api/v1/violations/process" in paths
        assert "/api/v1/violations/generate-declaration" in paths
        assert "/api/v1/violations/violations/tracks" not in paths

    def test_evidence_routes_match_frontend(self):
        paths = _route_paths()
        assert "/api/v1/motions/{motion_id}/evidence" in paths
        assert "/api/v1/motions/{motion_id}/evidence/upload" in paths
        assert "/api/v1/evidence/{evidence_id}" in paths
        assert "/api/v1/evidence/evidence/{evidence_id}" not in paths

    def test_gmail_routes_match_frontend(self):
        paths = _route_paths()
        assert "/api/v1/gmail/auth-url" in paths
        assert "/api/v1/gmail/exchange-code" in paths
        assert "/api/v1/motions/{motion_id}/gmail/scan" in paths
        assert "/api/v1/motions/{motion_id}/gmail/import" in paths

    def test_chat_pdf_prefix_not_doubled(self):
        paths = _route_paths()
        assert "/api/v1/chat-pdf/prepare-motion" in paths
        assert not any(p.startswith("/api/v1/chat-pdf/chat-pdf") for p in paths)


class TestMotionTypeCaseInsensitive:
    @pytest.mark.asyncio
    async def test_create_motion_accepts_lowercase(
        self, client: AsyncClient, auth_headers: dict
    ):
        resp = await client.post(
            "/api/v1/motions",
            json={"motion_type": "rfo", "title": "Lowercase type"},
            headers=auth_headers,
        )
        assert resp.status_code == 201, resp.text
        assert resp.json()["motion_type"] == "RFO"


async def _create_rfo_with_draft(client: AsyncClient, auth_headers: dict) -> str:
    """Profile + RFO motion + one draft; returns motion_id."""
    await client.post(
        "/api/v1/profiles",
        json={
            "case_number": "FL-2026-E2E",
            "county": "Los Angeles",
            "party_name": "Maria Vasquez",
            "other_party_name": "Daniel Reyes",
            "is_petitioner": True,
        },
        headers=auth_headers,
    )
    motion_resp = await client.post(
        "/api/v1/motions",
        json={"motion_type": "RFO", "title": "E2E regression RFO"},
        headers=auth_headers,
    )
    assert motion_resp.status_code == 201, motion_resp.text
    motion_id = motion_resp.json()["id"]

    draft_resp = await client.post(
        f"/api/v1/motions/{motion_id}/drafts",
        json={
            "step_number": 1,
            "step_name": "facts_circumstances",
            "question_data": {"changed_circumstances": "Nine late returns since March"},
        },
        headers=auth_headers,
    )
    assert draft_resp.status_code in (200, 201), draft_resp.text
    return motion_id


class TestMotionResponseCaseNumber:
    """Dashboard cards and PDF filenames read case_number off motion responses."""

    @pytest.mark.asyncio
    async def test_list_and_detail_include_profile_case_number(
        self, client: AsyncClient, auth_headers: dict
    ):
        motion_id = await _create_rfo_with_draft(client, auth_headers)

        list_resp = await client.get("/api/v1/motions/", headers=auth_headers)
        assert list_resp.status_code == 200
        assert list_resp.json()[0]["case_number"] == "FL-2026-E2E"

        detail_resp = await client.get(f"/api/v1/motions/{motion_id}", headers=auth_headers)
        assert detail_resp.status_code == 200
        assert detail_resp.json()["case_number"] == "FL-2026-E2E"


class TestDownloadConsistency:
    """Download must regenerate through the same generate_packet as generate-pdf-sync."""

    @pytest.mark.asyncio
    async def test_download_uses_packet_and_clean_filename(
        self, client: AsyncClient, auth_headers: dict
    ):
        fake_pdf = b"%PDF-1.4 packet bytes"
        motion_id = await _create_rfo_with_draft(client, auth_headers)

        with patch(
            "app.api.v1.endpoints.documents.generate_packet",
            new=AsyncMock(return_value=fake_pdf),
        ):
            sync_resp = await client.post(
                "/api/v1/documents/generate-pdf-sync",
                json={"motion_id": motion_id},
                headers=auth_headers,
            )
        assert sync_resp.status_code == 200, sync_resp.text

        list_resp = await client.get(
            f"/api/v1/documents/motion/{motion_id}/documents", headers=auth_headers
        )
        assert list_resp.status_code == 200
        doc = list_resp.json()["documents"][0]
        # Enum repr must not leak into user-facing filenames
        assert "MotionType." not in doc["filename"]
        assert "_RFO_" in doc["filename"]
        # Documents are regenerated on download, so they are always available
        assert doc["available"] is True

        with patch(
            "app.api.v1.endpoints.documents.generate_packet",
            new=AsyncMock(return_value=fake_pdf),
        ) as packet_mock:
            dl_resp = await client.get(
                f"/api/v1/documents/{doc['id']}/download", headers=auth_headers
            )
        assert dl_resp.status_code == 200, dl_resp.text
        assert dl_resp.headers["content-type"] == "application/pdf"
        assert dl_resp.content == fake_pdf
        assert packet_mock.await_count == 1

    @pytest.mark.asyncio
    async def test_async_generate_pdf_no_crash_and_correct_form(
        self, client: AsyncClient, auth_headers: dict
    ):
        motion_id = await _create_rfo_with_draft(client, auth_headers)
        resp = await client.post(
            "/api/v1/documents/generate-pdf",
            json={"motion_id": motion_id},
            headers=auth_headers,
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["status"] == "processing"

        list_resp = await client.get(
            f"/api/v1/documents/motion/{motion_id}/documents", headers=auth_headers
        )
        docs = list_resp.json()["documents"]
        # RFO must auto-detect to FL-300 (the request form), never FL-320
        assert all(d["document_type"] == "FL-300" for d in docs)
        assert all("MotionType." not in d["filename"] for d in docs)


class TestLLMServiceRobustness:
    def test_boots_without_gcp_and_without_explicit_mock(self):
        """USE_GCP=false + USE_MOCK_LLM=false must fall back to mock, not NameError."""
        import app.services.llm_service as llm_module

        saved = {
            key: os.environ.get(key)
            for key in ("USE_GCP", "USE_MOCK_LLM", "USE_CLAUDE")
        }
        os.environ.update(
            {"USE_GCP": "false", "USE_MOCK_LLM": "false", "USE_CLAUDE": "false"}
        )
        try:
            reloaded = importlib.reload(llm_module)
            assert reloaded.USE_MOCK_LLM is True
            assert reloaded.llm_service.model is None
        finally:
            for key, value in saved.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value
            importlib.reload(llm_module)

    @pytest.mark.asyncio
    async def test_mock_rewrite_returns_user_words_not_boilerplate(self):
        """Mock output lands in filing-ready PDFs — it must be the user's own words."""
        from app.services.llm_service import LLMService

        service = LLMService()
        result = await service.rewrite_rfo_section(
            section_name="facts_circumstances",
            user_answers={
                "changed_circumstances": "Daniel returned the children late nine times"
            },
            context={"party_role": "Petitioner", "county": "Los Angeles"},
        )
        assert result["success"] is True
        assert "MOCK LLM RESPONSE" not in result["rewritten_text"]
        assert "returned the children late" in result["rewritten_text"]

    @pytest.mark.asyncio
    async def test_mock_declaration_has_no_mock_boilerplate(self):
        from app.services.llm_service import LLMService

        service = LLMService()
        result = await service.rewrite_declaration(
            narrative="He was three hours late on May 17.",
            declarant_name="Maria Vasquez",
        )
        assert result["success"] is True
        text = result["rewritten_text"]
        assert "mock" not in text.lower()
        assert "Maria Vasquez" in text
        assert "perjury" in text.lower()
        assert "three hours late" in text
