"""
Exhibit Assembly Service — builds lettered exhibit pages to append to PDF packets.

Public API:
    assign_exhibit_letters(evidence: list[dict]) -> list[tuple[str, dict]]
    build_exhibit_pages(lettered: list[tuple[str, dict]]) -> bytes
    insert_exhibit_references(declaration_text: str, lettered: list[tuple[str, dict]]) -> str
"""
from __future__ import annotations

import io
import string
from typing import List, Tuple

import PyPDF2
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    PageBreak,
    Table,
    TableStyle,
)
from reportlab.lib import colors

# Sentinel for sorting items with null source_date after dated items.
_NULL_DATE_SENTINEL = "9999-99-99"


def _exhibit_letter(n: int) -> str:
    """Convert 0-based index to exhibit letter: 0→A, 25→Z, 26→AA, 27→AB …"""
    letters = string.ascii_uppercase
    if n < 26:
        return letters[n]
    # AA, AB, ... AZ, BA, ...
    first = letters[(n - 26) // 26]
    second = letters[(n - 26) % 26]
    return first + second


def assign_exhibit_letters(evidence: List[dict]) -> List[Tuple[str, dict]]:
    """Assign sequential exhibit letters to evidence items.

    Sorting: by source_date ascending (null dates last), then original order.

    Args:
        evidence: List of evidence dicts (shared shape). Items are NOT filtered
                  here — callers must pre-filter to confirmed+tagged items.

    Returns:
        List of (letter, item) tuples in exhibit order.
    """
    indexed = list(enumerate(evidence))
    indexed.sort(key=lambda pair: (
        pair[1].get("source_date") or _NULL_DATE_SENTINEL,
        pair[0],
    ))
    return [(_exhibit_letter(i), item) for i, (_, item) in enumerate(indexed)]


def build_exhibit_pages(lettered: List[Tuple[str, dict]]) -> bytes:
    """Build a PDF containing a cover page and one page per exhibit.

    Args:
        lettered: Output of assign_exhibit_letters (already filtered).

    Returns:
        PDF bytes.
    """
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=letter,
        leftMargin=inch,
        rightMargin=inch,
        topMargin=inch,
        bottomMargin=inch,
    )

    styles = getSampleStyleSheet()
    heading_style = ParagraphStyle(
        "ExhibitHeading",
        parent=styles["Heading1"],
        fontSize=16,
        spaceAfter=12,
        alignment=1,  # center
    )
    sub_style = ParagraphStyle(
        "ExhibitSub",
        parent=styles["Normal"],
        fontSize=11,
        spaceAfter=6,
    )
    body_style = styles["Normal"]

    story = []

    # --- Cover page ---
    story.append(Spacer(1, 1.5 * inch))
    story.append(Paragraph("EXHIBITS", heading_style))
    story.append(Spacer(1, 0.3 * inch))

    if lettered:
        table_data = [["Exhibit", "Date", "Description"]]
        for letter_str, item in lettered:
            table_data.append([
                letter_str,
                item.get("source_date") or "N/A",
                item.get("description") or "",
            ])
        tbl = Table(table_data, colWidths=[0.8 * inch, 1.3 * inch, 4.4 * inch])
        tbl.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(tbl)

    story.append(PageBreak())

    # --- One page per exhibit ---
    for letter_str, item in lettered:
        story.append(Paragraph(f"EXHIBIT {letter_str}", heading_style))

        date_val = item.get("source_date") or "N/A"
        story.append(Paragraph(f"<b>Date:</b> {date_val}", sub_style))

        desc = item.get("description") or ""
        story.append(Paragraph(f"<b>Description:</b> {desc}", sub_style))

        tags = item.get("tags") or []
        if tags:
            story.append(Paragraph(f"<b>Tags:</b> {', '.join(tags)}", sub_style))

        transcription = item.get("transcription")
        if transcription:
            story.append(Spacer(1, 0.15 * inch))
            story.append(Paragraph("<b>Transcription / Content:</b>", sub_style))
            # Split on newlines to preserve formatting
            for para_text in transcription.split("\n"):
                para_text = para_text.strip()
                if para_text:
                    story.append(Paragraph(para_text, body_style))
                    story.append(Spacer(1, 0.05 * inch))

        story.append(PageBreak())

    doc.build(story)
    buf.seek(0)
    return buf.read()


def insert_exhibit_references(
    declaration_text: str,
    lettered: List[Tuple[str, dict]],
) -> str:
    """Append a 'Supporting exhibits' paragraph to the declaration text.

    Purely mechanical — no LLM calls, no legal advice language.

    Args:
        declaration_text: The existing declaration body text.
        lettered:         Output of assign_exhibit_letters (filtered list).

    Returns:
        declaration_text unchanged when lettered is empty; otherwise the text
        with an appended paragraph listing all exhibits.
    """
    if not lettered:
        return declaration_text

    parts = []
    for letter_str, item in lettered:
        date_val = item.get("source_date") or "N/A"
        tags = item.get("tags") or []
        tag_str = ", ".join(tags) if tags else "other"
        ev_type = item.get("evidence_type") or "document"
        parts.append(f"Exhibit {letter_str} ({ev_type} dated {date_val}, {tag_str})")

    ref_paragraph = "\n\nSupporting exhibits: " + "; ".join(parts) + "."
    return declaration_text + ref_paragraph
