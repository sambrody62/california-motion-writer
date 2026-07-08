"""
Tests for POST /api/v1/llm/parse-served-motion — upload the served FL-300,
get structured prefill facts back. The file is parsed and never stored.
"""
import io
import pytest
from httpx import AsyncClient

from app.services import served_motion_parser as parser

ROUTE = "/api/v1/llm/parse-served-motion"


def _pdf_with_text() -> bytes:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    y = 750
    for line in (
        "REQUEST FOR ORDER (FL-300)",
        "Case Number: 24STFL01234",
        "Petitioner requests sole legal and physical custody of the minor",
        "children and guideline child support pursuant to Family Code 4055.",
    ):
        c.drawString(72, y, line)
        y -= 14
    c.save()
    return buf.getvalue()


class TestParseServedMotionEndpoint:
    @pytest.mark.asyncio
    async def test_requires_auth(self, client: AsyncClient):
        resp = await client.post(
            ROUTE, files={"file": ("motion.pdf", b"%PDF-fake", "application/pdf")}
        )
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_rejects_unsupported_extension(
        self, client: AsyncClient, auth_headers: dict
    ):
        resp = await client.post(
            ROUTE,
            files={"file": ("motion.docx", b"PK\x03\x04", "application/msword")},
            headers=auth_headers,
        )
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_rejects_oversized_file(
        self, client: AsyncClient, auth_headers: dict
    ):
        big = b"x" * (10 * 1024 * 1024 + 1)
        resp = await client.post(
            ROUTE,
            files={"file": ("motion.pdf", big, "application/pdf")},
            headers=auth_headers,
        )
        assert resp.status_code == 413

    @pytest.mark.asyncio
    async def test_mock_llm_returns_notice_and_empty_prefill(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Under the test env's mock LLM: 200, empty extracted, human notice."""
        resp = await client.post(
            ROUTE,
            files={"file": ("motion.pdf", _pdf_with_text(), "application/pdf")},
            headers=auth_headers,
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["success"] is True
        assert body["extracted"] == {}
        assert body["notice"] == parser.NOTICE_MOCK

    @pytest.mark.asyncio
    async def test_unreadable_file_returns_notice_not_error(
        self, client: AsyncClient, auth_headers: dict
    ):
        resp = await client.post(
            ROUTE,
            files={"file": ("motion.pdf", b"not really a pdf", "application/pdf")},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["extracted"] == {}
        assert body["notice"] == parser.NOTICE_UNREADABLE
