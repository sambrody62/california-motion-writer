"""
Tests for bulk text-screenshot import: POST /motions/{id}/evidence/batch-upload
(analysis only — persists nothing) and the text_thread_service that merges OCR
extractions into one conversation transcript.
"""
import pytest
from unittest.mock import AsyncMock
from httpx import AsyncClient

from app.services import text_thread_service as tts
from app.services import ocr_service
from app.services import llm_service as llm_backend


def _route(motion_id: str) -> str:
    return f"/api/v1/motions/{motion_id}/evidence/batch-upload"


async def _create_motion(client: AsyncClient, auth_headers: dict) -> str:
    resp = await client.post(
        "/api/v1/motions",
        json={"motion_type": "RFO", "title": "Batch test"},
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


def _files(n: int):
    return [("files", (f"shot-{i:02d}.png", b"fake-png-bytes", "image/png")) for i in range(n)]


OCR_TEXTS = {
    "shot-00.png": "Daniel: Running late again\n[Mar 3, 2026 8:41 PM]",
    "shot-01.png": "Me: You said 6pm. This is the fourth time.\n[Mar 3, 2026 8:42 PM]",
}


class TestThreadScreenshots:
    @pytest.mark.asyncio
    async def test_mock_llm_concatenates_in_order_with_notice(self, monkeypatch):
        monkeypatch.setattr(llm_backend, "USE_MOCK_LLM", True)
        generate = AsyncMock()
        monkeypatch.setattr(llm_backend.llm_service, "_generate", generate)

        ocr_texts = [
            {"filename": "a.png", "text": "first screenshot text"},
            {"filename": "b.png", "text": "second screenshot text"},
        ]
        result = await tts.thread_screenshots(ocr_texts)

        assert result["notice"] == tts.NOTICE_MOCK
        assert result["used_llm"] is False
        transcript = result["merged_transcript"]
        assert transcript.index("first screenshot") < transcript.index("second screenshot")
        assert "--- a.png ---" in transcript
        generate.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_llm_success_returns_merged_transcript(self, monkeypatch):
        monkeypatch.setattr(llm_backend, "USE_MOCK_LLM", False)
        monkeypatch.setattr(
            llm_backend.llm_service, "_generate",
            AsyncMock(return_value=(
                '{"transcript": "[2026-03-03 20:41] Daniel: Running late again",'
                ' "participants": ["Daniel", "Me"],'
                ' "date_start": "2026-03-03", "date_end": "2026-03-03"}',
                50, "claude-haiku-4-5",
            )),
        )
        result = await tts.thread_screenshots(
            [{"filename": "a.png", "text": "Daniel: Running late again"}]
        )
        assert result["notice"] is None
        assert result["used_llm"] is True
        assert "Running late again" in result["merged_transcript"]
        assert result["participants"] == ["Daniel", "Me"]
        assert result["suggested_source_date"] == "2026-03-03"

    @pytest.mark.asyncio
    async def test_llm_failure_falls_back_to_concat(self, monkeypatch):
        monkeypatch.setattr(llm_backend, "USE_MOCK_LLM", False)
        monkeypatch.setattr(
            llm_backend.llm_service, "_generate",
            AsyncMock(side_effect=RuntimeError("down")),
        )
        result = await tts.thread_screenshots(
            [{"filename": "a.png", "text": "some text"}]
        )
        assert result["notice"] == tts.NOTICE_LLM_FAILED
        assert "some text" in result["merged_transcript"]

    @pytest.mark.asyncio
    async def test_llm_bad_json_falls_back(self, monkeypatch):
        monkeypatch.setattr(llm_backend, "USE_MOCK_LLM", False)
        monkeypatch.setattr(
            llm_backend.llm_service, "_generate",
            AsyncMock(return_value=("not json at all", 10, "m")),
        )
        result = await tts.thread_screenshots(
            [{"filename": "a.png", "text": "some text"}]
        )
        assert result["notice"] == tts.NOTICE_LLM_FAILED
        assert "some text" in result["merged_transcript"]


class TestBatchUploadEndpoint:
    @pytest.mark.asyncio
    async def test_requires_auth(self, client: AsyncClient):
        resp = await client.post(_route("any-id"), files=_files(1))
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_foreign_motion_404(self, client: AsyncClient, auth_headers: dict):
        resp = await client.post(
            _route("00000000-0000-0000-0000-000000000000"),
            files=_files(1),
            headers=auth_headers,
        )
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_rejects_more_than_20_files(self, client: AsyncClient, auth_headers: dict):
        motion_id = await _create_motion(client, auth_headers)
        resp = await client.post(_route(motion_id), files=_files(21), headers=auth_headers)
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_rejects_non_image(self, client: AsyncClient, auth_headers: dict):
        motion_id = await _create_motion(client, auth_headers)
        resp = await client.post(
            _route(motion_id),
            files=[("files", ("notes.pdf", b"%PDF", "application/pdf"))],
            headers=auth_headers,
        )
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_ocr_disabled_returns_no_text_notice(
        self, client: AsyncClient, auth_headers: dict, monkeypatch
    ):
        monkeypatch.setattr(ocr_service, "ocr_enabled", lambda: False)
        motion_id = await _create_motion(client, auth_headers)
        resp = await client.post(_route(motion_id), files=_files(2), headers=auth_headers)
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["merged_transcript"] == ""
        assert body["notice"] == tts.NOTICE_NO_TEXT
        assert all(f["ok"] is False for f in body["per_file"])

    @pytest.mark.asyncio
    async def test_mock_llm_returns_concat_transcript_and_persists_nothing(
        self, client: AsyncClient, auth_headers: dict, monkeypatch
    ):
        monkeypatch.setattr(ocr_service, "ocr_enabled", lambda: True)
        monkeypatch.setattr(
            ocr_service, "extract_text",
            lambda content: OCR_TEXTS.get("shot-00.png", "fallback text"),
        )
        motion_id = await _create_motion(client, auth_headers)

        resp = await client.post(_route(motion_id), files=_files(2), headers=auth_headers)
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert "Running late again" in body["merged_transcript"]
        assert body["notice"]  # mock-LLM notice present
        assert len(body["per_file"]) == 2
        assert all(f["ok"] for f in body["per_file"])

        # analysis only — nothing persisted
        listing = await client.get(
            f"/api/v1/motions/{motion_id}/evidence", headers=auth_headers
        )
        assert listing.json() == []


class TestCreateEvidenceUserConfirmed:
    @pytest.mark.asyncio
    async def test_create_accepts_user_confirmed_true(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Bug-2: the review screen confirms in one step via create."""
        motion_id = await _create_motion(client, auth_headers)
        resp = await client.post(
            f"/api/v1/motions/{motion_id}/evidence",
            json={
                "evidence_type": "text",
                "tags": ["custody_violation"],
                "description": "Text conversation about late returns",
                "transcription": "[2026-03-03 20:41] Daniel: Running late again",
                "user_confirmed": True,
            },
            headers=auth_headers,
        )
        assert resp.status_code == 201, resp.text
        assert resp.json()["user_confirmed"] is True


class TestReadScreenshotImages:
    IMAGES = [
        {"filename": "a.png", "content": b"png-bytes", "media_type": "image/png"},
        {"filename": "b.jpg", "content": b"jpg-bytes", "media_type": "image/jpeg"},
    ]

    @pytest.mark.asyncio
    async def test_returns_none_under_mock_llm(self, monkeypatch):
        monkeypatch.setattr(llm_backend, "USE_MOCK_LLM", True)
        assert await tts.read_screenshot_images(self.IMAGES) is None

    @pytest.mark.asyncio
    async def test_returns_none_without_claude_backend(self, monkeypatch):
        monkeypatch.setattr(llm_backend, "USE_MOCK_LLM", False)
        monkeypatch.setattr(llm_backend.llm_service, "claude_backend", None)
        assert await tts.read_screenshot_images(self.IMAGES) is None

    @pytest.mark.asyncio
    async def test_success_returns_sanitized_thread(self, monkeypatch):
        monkeypatch.setattr(llm_backend, "USE_MOCK_LLM", False)
        backend = AsyncMock()
        backend.generate_with_images.return_value = (
            '{"transcript": "[2026-03-03 20:41] Daniel: Running late",'
            ' "participants": ["Daniel", "Me"],'
            ' "date_start": "03/03/2026", "date_end": null}',
            200, "claude-haiku-4-5",
        )
        monkeypatch.setattr(llm_backend.llm_service, "claude_backend", backend)

        result = await tts.read_screenshot_images(self.IMAGES)

        assert result is not None
        assert "Running late" in result["merged_transcript"]
        assert result["suggested_source_date"] == "2026-03-03"  # normalized
        assert result["notice"] is None
        assert result["used_llm"] is True
        # images were passed through as (bytes, media_type) pairs
        sent = backend.generate_with_images.await_args.args[1]
        assert sent == [(b"png-bytes", "image/png"), (b"jpg-bytes", "image/jpeg")]

    @pytest.mark.asyncio
    async def test_vision_failure_returns_none(self, monkeypatch):
        monkeypatch.setattr(llm_backend, "USE_MOCK_LLM", False)
        backend = AsyncMock()
        backend.generate_with_images.side_effect = RuntimeError("api down")
        monkeypatch.setattr(llm_backend.llm_service, "claude_backend", backend)
        assert await tts.read_screenshot_images(self.IMAGES) is None

    @pytest.mark.asyncio
    async def test_unparseable_output_returns_none(self, monkeypatch):
        monkeypatch.setattr(llm_backend, "USE_MOCK_LLM", False)
        backend = AsyncMock()
        backend.generate_with_images.return_value = ("no json here", 10, "m")
        monkeypatch.setattr(llm_backend.llm_service, "claude_backend", backend)
        assert await tts.read_screenshot_images(self.IMAGES) is None


class TestBatchUploadVisionPath:
    @pytest.mark.asyncio
    async def test_vision_result_used_without_ocr(
        self, client: AsyncClient, auth_headers: dict, monkeypatch
    ):
        """When vision succeeds, OCR is never consulted and nothing persists."""
        def _no_ocr(*a, **k):
            raise AssertionError("OCR must not run when vision succeeds")

        monkeypatch.setattr(ocr_service, "extract_text", _no_ocr)

        async def _vision(images, user_id=None):
            return {
                "merged_transcript": "[2026-03-03 20:41] Daniel: Running late",
                "participants": ["Daniel", "Me"],
                "date_range": {"start": "2026-03-03", "end": "2026-03-03"},
                "suggested_source_date": "2026-03-03",
                "notice": None,
                "used_llm": True,
            }

        monkeypatch.setattr(tts, "read_screenshot_images", _vision)

        motion_id = await _create_motion(client, auth_headers)
        resp = await client.post(_route(motion_id), files=_files(2), headers=auth_headers)
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert "Running late" in body["merged_transcript"]
        assert body["notice"] is None
        assert all(f["ok"] for f in body["per_file"])

        listing = await client.get(
            f"/api/v1/motions/{motion_id}/evidence", headers=auth_headers
        )
        assert listing.json() == []

    @pytest.mark.asyncio
    async def test_oversized_image_excluded_from_vision(
        self, client: AsyncClient, auth_headers: dict, monkeypatch
    ):
        received = {}

        async def _vision(images, user_id=None):
            received["filenames"] = [i["filename"] for i in images]
            return {
                "merged_transcript": "t", "participants": [],
                "date_range": {"start": None, "end": None},
                "suggested_source_date": None, "notice": None, "used_llm": True,
            }

        monkeypatch.setattr(tts, "read_screenshot_images", _vision)
        monkeypatch.setattr(ocr_service, "ocr_enabled", lambda: False)

        big = b"x" * (5 * 1024 * 1024)  # over the 4.5MB per-image vision cap
        files = [
            ("files", ("small.png", b"tiny", "image/png")),
            ("files", ("huge.png", big, "image/png")),
        ]
        motion_id = await _create_motion(client, auth_headers)
        resp = await client.post(_route(motion_id), files=files, headers=auth_headers)
        assert resp.status_code == 200, resp.text
        assert received["filenames"] == ["small.png"]
        per_file = {f["filename"]: f for f in resp.json()["per_file"]}
        assert per_file["small.png"]["ok"] is True
        assert per_file["huge.png"]["ok"] is False

    @pytest.mark.asyncio
    async def test_vision_none_falls_back_to_existing_path(
        self, client: AsyncClient, auth_headers: dict, monkeypatch
    ):
        """Vision unavailable (mock env) → OCR-disabled manual path unchanged."""
        monkeypatch.setattr(ocr_service, "ocr_enabled", lambda: False)
        motion_id = await _create_motion(client, auth_headers)
        resp = await client.post(_route(motion_id), files=_files(2), headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["notice"] == tts.NOTICE_NO_TEXT
