"""
Tests for served_motion_parser — extracting structured facts from an uploaded
FL-300 so the FL-320 response wizard can be pre-filled.
"""
import io
import pytest
from unittest.mock import AsyncMock

from app.services import served_motion_parser as parser
from app.services import llm_service as llm_backend


def _text_pdf_bytes(text: str) -> bytes:
    """Build an in-memory single-page PDF with a real text layer."""
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    y = 750
    for line in text.splitlines():
        c.drawString(72, y, line)
        y -= 14
    c.save()
    return buf.getvalue()


class TestParseLlmJson:
    def test_plain_json(self):
        assert parser.parse_llm_json('{"case_number": "24STFL01234"}') == {
            "case_number": "24STFL01234"
        }

    def test_fenced_json(self):
        raw = '```json\n{"case_number": "24STFL01234"}\n```'
        assert parser.parse_llm_json(raw) == {"case_number": "24STFL01234"}

    def test_garbage_returns_empty(self):
        assert parser.parse_llm_json("I could not find any JSON here.") == {}

    def test_non_object_returns_empty(self):
        assert parser.parse_llm_json('["a", "b"]') == {}


class TestSanitizeExtracted:
    def test_whitelist_and_date_served_never_passes(self):
        out = parser.sanitize_extracted(
            {
                "case_number": "24STFL01234",
                "petitioner_name": "Angela Mendoza",
                "date_served": "2026-06-01",
                "malicious_key": "x",
            }
        )
        assert out["case_number"] == "24STFL01234"
        assert out["petitioner_name"] == "Angela Mendoza"
        assert "date_served" not in out
        assert "malicious_key" not in out

    @pytest.mark.parametrize(
        "raw,expected",
        [
            ("2026-08-15", "2026-08-15"),
            ("08/15/2026", "2026-08-15"),
            ("August 15, 2026", "2026-08-15"),
            ("Aug 15, 2026", "2026-08-15"),
            ("someday soon", None),
        ],
    )
    def test_hearing_date_normalized(self, raw, expected):
        out = parser.sanitize_extracted({"hearing_date": raw})
        assert out.get("hearing_date") == expected

    @pytest.mark.parametrize(
        "raw,expected",
        [
            ("8:30 AM", "08:30"),
            ("14:00", "14:00"),
            ("1:30 PM", "13:30"),
            ("morning", None),
        ],
    )
    def test_hearing_time_normalized(self, raw, expected):
        out = parser.sanitize_extracted({"hearing_time": raw})
        assert out.get("hearing_time") == expected

    def test_other_party_requests_capped(self):
        out = parser.sanitize_extracted({"other_party_requests": "x" * 5000})
        assert len(out["other_party_requests"]) <= 2000

    def test_nulls_and_non_strings_dropped(self):
        out = parser.sanitize_extracted({"case_number": None, "petitioner_name": 42})
        assert "case_number" not in out
        assert "petitioner_name" not in out

    def test_children_list_passes_through(self):
        children = [{"name": "Diego", "age": 6}]
        out = parser.sanitize_extracted({"children": children})
        assert out["children"] == children

    def test_children_non_list_dropped(self):
        assert "children" not in parser.sanitize_extracted({"children": "Diego"})


class TestChildrenValidatedAgainstDocument:
    """Extracted children must exist in the uploaded document (finding L3:
    the extractor invented Mateo 'age 3' found nowhere in the document)."""

    DOC = (
        "REQUEST FOR ORDER (FL-300)\n"
        "The children of the marriage are Sofia Delgado, 6 years old, and "
        "Mateo Delgado, who is 4 years of age."
    )

    def test_age_not_near_name_is_dropped_but_child_kept(self):
        out = parser.sanitize_extracted(
            {"children": [{"name": "Mateo", "age": 3}]}, self.DOC
        )
        assert out["children"] == [{"name": "Mateo", "age": None}]

    def test_age_near_name_is_kept(self):
        out = parser.sanitize_extracted(
            {"children": [{"name": "Sofia Delgado", "age": 6}]}, self.DOC
        )
        assert out["children"] == [{"name": "Sofia Delgado", "age": 6}]

    def test_child_absent_from_document_is_dropped(self):
        out = parser.sanitize_extracted(
            {"children": [{"name": "Diego", "age": 5}]}, self.DOC
        )
        assert "children" not in out

    def test_empty_document_text_keeps_current_behavior(self):
        children = [{"name": "Diego", "age": 6}]
        out = parser.sanitize_extracted({"children": children}, "")
        assert out["children"] == children


class TestExtractDocumentText:
    def test_text_pdf(self):
        content = _text_pdf_bytes(
            "REQUEST FOR ORDER (FL-300)\nCase Number: 24STFL01234\n"
            "Petitioner requests modification of child custody and visitation.\n"
            "Hearing date: August 15, 2026 at 8:30 AM in Department 2."
        )
        text, notice = parser.extract_document_text(content, "pdf")
        assert "24STFL01234" in text
        assert notice is None

    def test_scanned_pdf_gets_unreadable_notice(self):
        # A valid PDF whose pages carry no text layer
        content = _text_pdf_bytes("")
        text, notice = parser.extract_document_text(content, "pdf")
        assert text == ""
        assert notice == parser.NOTICE_UNREADABLE

    def test_garbage_pdf_bytes(self):
        text, notice = parser.extract_document_text(b"not a pdf at all", "pdf")
        assert text == ""
        assert notice == parser.NOTICE_UNREADABLE

    def test_image_with_ocr_disabled(self, monkeypatch):
        monkeypatch.setattr(parser.ocr_service, "ocr_enabled", lambda: False)
        text, notice = parser.extract_document_text(b"fake-image-bytes", "jpg")
        assert text == ""
        assert notice == parser.NOTICE_UNREADABLE

    def test_image_with_ocr_enabled(self, monkeypatch):
        monkeypatch.setattr(parser.ocr_service, "ocr_enabled", lambda: True)
        monkeypatch.setattr(
            parser.ocr_service,
            "extract_text",
            lambda b: "REQUEST FOR ORDER (FL-300) " * 10,
        )
        text, notice = parser.extract_document_text(b"fake-image-bytes", "jpg")
        assert "REQUEST FOR ORDER" in text
        assert notice is None


class TestParseServedMotion:
    CONTENT = None  # built once in setup

    @classmethod
    def setup_class(cls):
        cls.CONTENT = _text_pdf_bytes(
            "REQUEST FOR ORDER (FL-300)\nCase Number: 24STFL01234\n"
            "Petitioner: Angela Mendoza\n"
            "Petitioner requests sole legal and physical custody of the minor\n"
            "children and guideline child support pursuant to Family Code 4055."
        )

    @pytest.mark.asyncio
    async def test_mock_llm_short_circuits(self, monkeypatch):
        """Under USE_MOCK_LLM the LLM is never called; empty prefill + notice."""
        monkeypatch.setattr(llm_backend, "USE_MOCK_LLM", True)
        generate = AsyncMock()
        monkeypatch.setattr(llm_backend.llm_service, "_generate", generate)

        result = await parser.parse_served_motion(self.CONTENT, "pdf")

        assert result["extracted"] == {}
        assert result["notice"] == parser.NOTICE_MOCK
        generate.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_llm_extraction_happy_path(self, monkeypatch):
        monkeypatch.setattr(llm_backend, "USE_MOCK_LLM", False)
        generate = AsyncMock(
            return_value=(
                '{"case_number": "24STFL01234", "petitioner_name": "Angela Mendoza",'
                ' "hearing_date": "08/15/2026", "date_served": "2026-06-01",'
                ' "other_party_requests": "Sole custody and child support"}',
                100,
                "claude-haiku-4-5",
            )
        )
        monkeypatch.setattr(llm_backend.llm_service, "_generate", generate)

        result = await parser.parse_served_motion(self.CONTENT, "pdf")

        assert result["notice"] is None
        extracted = result["extracted"]
        assert extracted["case_number"] == "24STFL01234"
        assert extracted["hearing_date"] == "2026-08-15"
        assert extracted["other_party_requests"] == "Sole custody and child support"
        assert "date_served" not in extracted
        # the document text must have reached the prompt
        prompt = generate.await_args.args[0]
        assert "24STFL01234" in prompt

    @pytest.mark.asyncio
    async def test_llm_failure_returns_notice(self, monkeypatch):
        monkeypatch.setattr(llm_backend, "USE_MOCK_LLM", False)
        monkeypatch.setattr(
            llm_backend.llm_service,
            "_generate",
            AsyncMock(side_effect=RuntimeError("backend down")),
        )

        result = await parser.parse_served_motion(self.CONTENT, "pdf")

        assert result["extracted"] == {}
        assert result["notice"] == parser.NOTICE_LLM_FAILED

    @pytest.mark.asyncio
    async def test_unreadable_document_skips_llm(self, monkeypatch):
        monkeypatch.setattr(llm_backend, "USE_MOCK_LLM", False)
        generate = AsyncMock()
        monkeypatch.setattr(llm_backend.llm_service, "_generate", generate)

        result = await parser.parse_served_motion(b"not a pdf", "pdf")

        assert result["extracted"] == {}
        assert result["notice"] == parser.NOTICE_UNREADABLE
        generate.assert_not_awaited()
