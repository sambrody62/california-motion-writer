"""
Court-ready exhibit packet formatting — purely mechanical, no LLM.

Produces what a clerk expects to see:
  - declarant authentication language ("true and correct copy of ...")
  - an INDEX OF EXHIBITS with page numbers
  - the case caption on every exhibit page
  - "Page N of M" stamps

Public API:
    build_authentication_text(lettered) -> str
    build_exhibit_packet(lettered, caption) -> bytes
"""
from __future__ import annotations

import io
import math
from functools import partial
from typing import Dict, List, Tuple

import PyPDF2
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.services.exhibit_assembly_service import _exhibit_story

_TYPE_NOUNS = {
    "text": "a text message record",
    "email": "an email",
    "photo": "a photograph",
    "document": "a document",
}
# Conservative: a row is ~22pt (10pt font + padding); 22 rows + header + title
# always fit inside letter-size margins, so chunk page count stays deterministic
_INDEX_ROWS_PER_PAGE = 22
_INDEX_DESC_MAX = 60


def build_authentication_text(lettered: List[Tuple[str, dict]]) -> str:
    """Declarant authentication paragraphs, one per exhibit; '' when empty.

    Appended to the declaration (signed under penalty of perjury), which is how
    exhibits are authenticated in California family court filings.
    """
    paragraphs = []
    for letter_str, item in lettered:
        noun = _TYPE_NOUNS.get(item.get("evidence_type") or "", "a document")
        date_val = item.get("source_date")
        dated = f" dated {date_val}" if date_val else ""
        desc = (item.get("description") or "").strip()
        paragraphs.append(
            f"Attached hereto as Exhibit {letter_str} is a true and correct copy "
            f"of {noun}{dated}, described as: {desc}"
        )
    return "\n\n".join(paragraphs)


def _caption_line(caption: Dict[str, str]) -> str:
    return (
        f"Case No. {caption.get('case_number') or 'N/A'} — "
        f"{caption.get('party_name') or ''} v. {caption.get('other_party_name') or ''}"
    )


def _caption_header(canv, doc, caption: Dict[str, str]) -> None:
    canv.saveState()
    canv.setFont("Helvetica", 9)
    canv.drawString(inch, 10.55 * inch, _caption_line(caption))
    canv.restoreState()


def _render_story(story: list, caption: Dict[str, str]) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=letter,
        leftMargin=inch,
        rightMargin=inch,
        topMargin=inch,
        bottomMargin=inch,
    )
    header = partial(_caption_header, caption=caption)
    doc.build(story, onFirstPage=header, onLaterPages=header)
    buf.seek(0)
    return buf.read()


def _page_count(pdf_bytes: bytes) -> int:
    return len(PyPDF2.PdfReader(io.BytesIO(pdf_bytes)).pages)


def _index_table(rows: List[Tuple[str, str, str, int]]) -> Table:
    table_data = [["Exhibit", "Date", "Description", "Page"]]
    for letter_str, date_val, desc, page in rows:
        if len(desc) > _INDEX_DESC_MAX:
            desc = desc[: _INDEX_DESC_MAX - 1] + "…"
        table_data.append([letter_str, date_val or "N/A", desc, str(page)])
    tbl = Table(table_data, colWidths=[0.7 * inch, 1.2 * inch, 3.9 * inch, 0.7 * inch])
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return tbl


def _render_index(rows: List[Tuple[str, str, str, int]], caption: Dict[str, str]) -> bytes:
    """Index pages, chunked so the page count is exactly ceil(rows/28)."""
    styles = getSampleStyleSheet()
    heading = ParagraphStyle(
        "IndexHeading", parent=styles["Heading1"], fontSize=16, spaceAfter=12, alignment=1
    )
    story: list = []
    for start in range(0, len(rows), _INDEX_ROWS_PER_PAGE):
        if start:
            story.append(PageBreak())
        story.append(Spacer(1, 0.3 * inch))
        story.append(Paragraph("INDEX OF EXHIBITS", heading))
        story.append(Spacer(1, 0.2 * inch))
        story.append(_index_table(rows[start:start + _INDEX_ROWS_PER_PAGE]))
    return _render_story(story, caption)


def _merge(parts: List[bytes]) -> bytes:
    writer = PyPDF2.PdfWriter()
    for part in parts:
        for page in PyPDF2.PdfReader(io.BytesIO(part)).pages:
            writer.add_page(page)
    buf = io.BytesIO()
    writer.write(buf)
    buf.seek(0)
    return buf.read()


def _stamp_page_numbers(pdf_bytes: bytes) -> bytes:
    reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
    writer = PyPDF2.PdfWriter()
    total = len(reader.pages)
    for i, page in enumerate(reader.pages):
        buf = io.BytesIO()
        canv = rl_canvas.Canvas(buf, pagesize=letter)
        canv.setFont("Helvetica", 9)
        canv.drawRightString(7.5 * inch, 0.5 * inch, f"Page {i + 1} of {total}")
        canv.save()
        buf.seek(0)
        page.merge_page(PyPDF2.PdfReader(buf).pages[0])
        writer.add_page(page)
    out = io.BytesIO()
    writer.write(out)
    out.seek(0)
    return out.read()


def build_exhibit_packet(lettered: List[Tuple[str, dict]], caption: Dict[str, str]) -> bytes:
    """Index-first exhibit packet with caption headers and page stamps.

    Two-pass build: render each exhibit alone to learn its page count, compute
    start pages (index pages included in the numbering), then render the index
    and merge everything.
    """
    if not lettered:
        return _render_story([Paragraph("EXHIBITS", getSampleStyleSheet()["Heading1"])], caption)

    exhibit_pdfs = [_render_story(_exhibit_story(l, item), caption) for l, item in lettered]
    counts = [_page_count(p) for p in exhibit_pdfs]

    index_page_count = math.ceil(len(lettered) / _INDEX_ROWS_PER_PAGE)
    rows: List[Tuple[str, str, str, int]] = []
    start = index_page_count + 1
    for (letter_str, item), count in zip(lettered, counts):
        rows.append((letter_str, item.get("source_date") or "", item.get("description") or "", start))
        start += count

    index_pdf = _render_index(rows, caption)
    return _stamp_page_numbers(_merge([index_pdf] + exhibit_pdfs))
