"""
Tests for exhibit_formatting — court-ready exhibit packets: authentication
language, INDEX OF EXHIBITS with page numbers, case-caption headers, and
"Page N of M" stamps. Purely mechanical; no LLM involvement.
"""
import io
import re
import pytest
import PyPDF2

from app.services import exhibit_formatting as fmt
from app.services.exhibit_assembly_service import assign_exhibit_letters

CAPTION = {
    "case_number": "24STFL01234",
    "party_name": "Maria Vasquez",
    "other_party_name": "Daniel Reyes",
}


def _evidence(n=2, transcription="Short content line."):
    items = [
        {
            "evidence_type": "email",
            "source_date": "2026-03-01",
            "description": "DESC-A payment overdue email",
            "tags": ["non_payment"],
            "transcription": transcription,
            "user_confirmed": True,
        },
        {
            "evidence_type": "text",
            "source_date": "2026-04-02",
            "description": "DESC-B late return text",
            "tags": ["custody_violation"],
            "transcription": transcription,
            "user_confirmed": True,
        },
    ]
    return items[:n]


def _page_texts(pdf_bytes: bytes):
    reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
    return [(page.extract_text() or "") for page in reader.pages]


class TestAuthenticationText:
    def test_empty_list_returns_empty(self):
        assert fmt.build_authentication_text([]) == ""

    def test_contains_true_and_correct_copy_per_exhibit(self):
        lettered = assign_exhibit_letters(_evidence())
        text = fmt.build_authentication_text(lettered)
        assert text.count("true and correct copy") == 2
        assert "Attached hereto as Exhibit A" in text
        assert "Attached hereto as Exhibit B" in text

    def test_includes_type_noun_date_and_description(self):
        lettered = assign_exhibit_letters(_evidence())
        text = fmt.build_authentication_text(lettered)
        assert "an email dated 2026-03-01" in text
        assert "a text message record dated 2026-04-02" in text
        assert "DESC-A payment overdue email" in text

    def test_null_date_omits_dated_clause(self):
        items = _evidence(1)
        items[0]["source_date"] = None
        lettered = assign_exhibit_letters(items)
        text = fmt.build_authentication_text(lettered)
        assert "dated" not in text
        assert "true and correct copy of an email, described as" in text


class TestExhibitPacket:
    def test_valid_pdf_with_index_heading(self):
        lettered = assign_exhibit_letters(_evidence())
        pdf = fmt.build_exhibit_packet(lettered, CAPTION)
        assert pdf.startswith(b"%PDF")
        pages = _page_texts(pdf)
        assert "INDEX OF EXHIBITS" in pages[0]

    def test_index_page_numbers_match_actual_exhibit_pages(self):
        lettered = assign_exhibit_letters(_evidence())
        pdf = fmt.build_exhibit_packet(lettered, CAPTION)
        pages = _page_texts(pdf)

        for marker, desc in (("EXHIBIT A", "DESC-A"), ("EXHIBIT B", "DESC-B")):
            actual = next(
                i + 1 for i, t in enumerate(pages)
                if marker in t and "INDEX OF" not in t
            )
            m = re.search(re.escape(desc) + r".*?(\d+)", pages[0].replace("\n", " "))
            assert m, f"index row for {desc} not found"
            assert int(m.group(1)) == actual

    def test_caption_header_on_every_page(self):
        lettered = assign_exhibit_letters(_evidence())
        pdf = fmt.build_exhibit_packet(lettered, CAPTION)
        for i, text in enumerate(_page_texts(pdf)):
            assert "24STFL01234" in text, f"caption missing on page {i + 1}"

    def test_page_numbers_stamped_n_of_m(self):
        lettered = assign_exhibit_letters(_evidence())
        pdf = fmt.build_exhibit_packet(lettered, CAPTION)
        pages = _page_texts(pdf)
        total = len(pages)
        assert f"Page 1 of {total}" in pages[0]
        assert f"Page {total} of {total}" in pages[-1]

    def test_multipage_transcription_shifts_subsequent_start_pages(self):
        long_transcription = "\n".join(
            f"Line {i}: message content that fills space." for i in range(150)
        )
        items = _evidence()
        items[0]["transcription"] = long_transcription
        lettered = assign_exhibit_letters(items)
        pdf = fmt.build_exhibit_packet(lettered, CAPTION)
        pages = _page_texts(pdf)

        actual_b = next(
            i + 1 for i, t in enumerate(pages)
            if "EXHIBIT B" in t and "INDEX OF" not in t
        )
        assert actual_b > 3  # index + multi-page Exhibit A push B past page 3
        m = re.search(r"DESC-B.*?(\d+)", pages[0].replace("\n", " "))
        assert m and int(m.group(1)) == actual_b

    def test_more_exhibits_than_one_index_page_holds(self):
        items = [
            {
                "evidence_type": "document",
                "source_date": f"2026-01-{(i % 28) + 1:02d}",
                "description": f"DESC-{i:02d}",
                "tags": ["other"],
                "transcription": "x",
                "user_confirmed": True,
            }
            for i in range(30)
        ]
        lettered = assign_exhibit_letters(items)
        pdf = fmt.build_exhibit_packet(lettered, CAPTION)
        pages = _page_texts(pdf)
        assert "INDEX OF EXHIBITS" in pages[0]
        assert "INDEX OF EXHIBITS" in pages[1]  # continuation page
        # first exhibit starts right after the two index pages
        first_exhibit_page = next(
            i + 1 for i, t in enumerate(pages)
            if "EXHIBIT A" in t and "INDEX OF" not in t
        )
        assert first_exhibit_page == 3

    def test_no_llm_call(self, monkeypatch):
        from app.services import llm_service as llm_backend

        def _explode(*a, **k):
            raise AssertionError("exhibit formatting must never call the LLM")

        monkeypatch.setattr(llm_backend.llm_service, "_generate", _explode)
        lettered = assign_exhibit_letters(_evidence())
        assert fmt.build_authentication_text(lettered)
        assert fmt.build_exhibit_packet(lettered, CAPTION).startswith(b"%PDF")
