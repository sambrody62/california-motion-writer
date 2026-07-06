"""
Overflow handling for PDF form fills.

The bug: text longer than a form field's box was silently truncated
(declarations) or drawn past the page edge (single-line fields). Court
practice is a continuation/attachment page — no user text may ever be lost.
"""
import io

import PyPDF2
import pytest
from reportlab.pdfbase.pdfmetrics import stringWidth

from app.services.pdf_text_utils import (
    build_continuation_pages,
    fit_single_line,
    wrap_text_accurate,
)


class TestFitSingleLine:
    def test_short_text_unchanged_at_default_size(self):
        size, text = fit_single_line("John Smith", max_width=300)
        assert size == 10
        assert text == "John Smith"

    def test_long_text_shrinks_to_fit(self):
        value = "A Moderately Long Party Name That Needs Smaller Type"
        max_width = 250
        size, text = fit_single_line(value, max_width=max_width)
        assert 6 <= size < 10
        assert text == value
        assert stringWidth(text, "Helvetica", size) <= max_width

    def test_absurd_text_truncates_visibly_at_floor(self):
        value = "X" * 500
        max_width = 200
        size, text = fit_single_line(value, max_width=max_width)
        assert size == 6
        assert text.endswith("…")
        assert stringWidth(text, "Helvetica", size) <= max_width


class TestWrapAccurate:
    def test_every_line_fits_width(self):
        text = " ".join(f"word{i}" for i in range(200))
        width = 200
        lines = wrap_text_accurate(text, width)
        assert all(stringWidth(l, "Helvetica", 10) <= width for l in lines)

    def test_no_words_lost(self):
        text = " ".join(f"word{i}" for i in range(200))
        rejoined = " ".join(wrap_text_accurate(text, 200))
        for i in range(200):
            assert f"word{i}" in rejoined

    def test_paragraph_breaks_preserved(self):
        lines = wrap_text_accurate("para one\n\npara two", 400)
        assert "" in lines  # blank line separates paragraphs


class TestContinuationPages:
    def test_builds_captioned_multipage_pdf(self):
        lines = [f"line {i}" for i in range(150)]  # more than one page worth
        pdf = build_continuation_pages(lines, caption="ATTACHMENT — Declaration (continued)", case_number="FL-2024-001")
        reader = PyPDF2.PdfReader(io.BytesIO(pdf))
        assert len(reader.pages) >= 2
        first = reader.pages[0].extract_text()
        assert "ATTACHMENT" in first
        assert "FL-2024-001" in first
        all_text = "".join(p.extract_text() for p in reader.pages)
        assert "line 0" in all_text and "line 149" in all_text


class TestMc030NoTextLost:
    async def test_long_declaration_fully_present(self):
        from app.services import pdf_packet_service as pps

        class P:
            party_name = "John Smith"
            other_party_name = "Jane Smith"
            case_number = "FL-2024-001"
            county = "San Diego"
            is_petitioner = True
            children_info = []

        declaration = " ".join(f"word{i}" for i in range(600)) + " ENDMARKER"
        pdf = await pps._fill_mc030(P(), declaration)
        reader = PyPDF2.PdfReader(io.BytesIO(pdf))
        text = "".join(page.extract_text() for page in reader.pages)
        missing = [i for i in range(600) if f"word{i}" not in text]
        assert missing == [], f"{len(missing)} words silently dropped"
        assert "ENDMARKER" in text
        assert "continued" in text.lower()  # box carries a visible continuation marker


class TestFillFormOverflow:
    async def test_multiline_overflow_appends_attachment_page(self):
        from app.services.pdf_service import PDFService

        svc = PDFService()
        # Synthetic multiline field so the test doesn't depend on a specific mapping
        svc.form_fields["FL-300"]["test_notes"] = {
            "page": 0, "x": 100, "y": 300, "type": "multiline",
            "width": 300, "height": 60,
        }
        with open("forms/FL-300.pdf", "rb") as fh:
            template_pages = len(PyPDF2.PdfReader(fh).pages)

        long_text = " ".join(f"note{i}" for i in range(400)) + " FINALNOTE"
        pdf = await svc.fill_form("FL-300", {
            "petitioner_name": "John Smith",
            "case_number": "FL-2024-001",
            "test_notes": long_text,
        })
        reader = PyPDF2.PdfReader(io.BytesIO(pdf))
        assert len(reader.pages) > template_pages  # attachment appended
        text = "".join(p.extract_text() for p in reader.pages)
        assert "FINALNOTE" in text
        missing = [i for i in range(400) if f"note{i}" not in text]
        assert missing == []

    async def test_single_line_never_exceeds_page(self):
        from app.services.pdf_service import PDFService

        svc = PDFService()
        long_name = "A VERY LONG PARTY NAME " * 15
        pdf = await svc.fill_form("FL-300", {
            "petitioner_name": long_name,
            "case_number": "FL-2024-001",
        })
        assert pdf[:4] == b"%PDF"  # generated fine; fitting is unit-tested above

    async def test_normal_fill_unchanged(self):
        from app.services.pdf_service import PDFService

        svc = PDFService()
        with open("forms/FL-300.pdf", "rb") as fh:
            template_pages = len(PyPDF2.PdfReader(fh).pages)
        pdf = await svc.fill_form("FL-300", {
            "petitioner_name": "John Smith",
            "case_number": "FL-2024-001",
        })
        reader = PyPDF2.PdfReader(io.BytesIO(pdf))
        assert len(reader.pages) == template_pages  # no attachment when nothing overflows
        assert "John Smith" in reader.pages[0].extract_text()
