"""
Finding L18: during the 129s process-motion the backend kept issuing paid
Anthropic calls after the browser disconnected. process_complete_motion now
takes an optional async should_abort callable checked before each section,
and the endpoint wires it to http_request.is_disconnected.
"""
import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock

from starlette.requests import Request

from app.services.llm_service import LLMService

pytestmark = pytest.mark.asyncio

_REWRITE_OK = {
    "success": True,
    "rewritten_text": "ok",
    "tokens_used": 5,
    "model": "mock-llm",
}

DRAFTS = [
    {"step_number": n, "step_name": f"step_{n}", "question_data": {"a": f"answer {n}"}}
    for n in (1, 2, 3)
]


class TestServiceAbort:
    async def test_abort_stops_remaining_sections(self, monkeypatch):
        service = LLMService()
        rewrite = AsyncMock(return_value=_REWRITE_OK)
        monkeypatch.setattr(service, "rewrite_rfo_section", rewrite)

        result = await service.process_complete_motion(
            motion_type="RFO",
            all_drafts=DRAFTS,
            profile_data={},
            should_abort=AsyncMock(side_effect=[False, True]),
        )

        assert rewrite.await_count == 1
        assert result["aborted"] is True
        assert len(result["sections"]) == 1

    async def test_no_should_abort_processes_everything(self, monkeypatch):
        service = LLMService()
        rewrite = AsyncMock(return_value=_REWRITE_OK)
        monkeypatch.setattr(service, "rewrite_rfo_section", rewrite)

        result = await service.process_complete_motion(
            motion_type="RFO", all_drafts=DRAFTS, profile_data={}
        )

        assert rewrite.await_count == 3
        assert result["aborted"] is False


async def _motion_with_drafts(client: AsyncClient, headers: dict) -> str:
    resp = await client.post(
        "/api/v1/motions/",
        json={"motion_type": "RFO", "title": "Disconnect test"},
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    motion_id = resp.json()["id"]
    for n in (1, 2, 3):
        resp = await client.post(
            f"/api/v1/motions/{motion_id}/drafts",
            json={
                "step_number": n,
                "step_name": f"step_{n}",
                "question_data": {"a": f"answer {n}"},
            },
            headers=headers,
        )
        assert resp.status_code == 200, resp.text
    return motion_id


class TestEndpointDisconnect:
    async def test_disconnected_client_stops_processing(
        self, client: AsyncClient, auth_headers: dict, monkeypatch
    ):
        motion_id = await _motion_with_drafts(client, auth_headers)
        monkeypatch.setattr(
            Request, "is_disconnected", AsyncMock(return_value=True)
        )

        resp = await client.post(
            "/api/v1/llm/process-motion",
            json={"motion_id": motion_id},
            headers=auth_headers,
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["sections_processed"] == 0

        detail = await client.get(f"/api/v1/motions/{motion_id}", headers=auth_headers)
        body = detail.json()
        assert body["status"] == "draft"
        assert all(d["llm_output"] is None for d in body["drafts"])

    async def test_connected_client_processes_all_sections(
        self, client: AsyncClient, auth_headers: dict, monkeypatch
    ):
        motion_id = await _motion_with_drafts(client, auth_headers)
        monkeypatch.setattr(
            Request, "is_disconnected", AsyncMock(return_value=False)
        )

        resp = await client.post(
            "/api/v1/llm/process-motion",
            json={"motion_id": motion_id},
            headers=auth_headers,
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["sections_processed"] == 3

        detail = await client.get(f"/api/v1/motions/{motion_id}", headers=auth_headers)
        assert all(d["llm_output"] for d in detail.json()["drafts"])
