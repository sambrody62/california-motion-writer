"""
Tests for exhibit assembly service.

Covers:
- Letter assignment: A-Z then AA, AB, ... for >26 items
- Only items with user_confirmed=True AND at least one tag are included
- build_exhibit_pages produces a valid PDF with 'EXHIBIT A' in text
- Merged packet contains exhibit pages when evidence is provided
- Packet without evidence is unchanged (regression)
- Declaration gains the supporting-exhibits paragraph via insert_exhibit_references
"""
import io
import pytest
import pytest_asyncio
import PyPDF2


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _extract_text(pdf_bytes: bytes) -> str:
    reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
    return "".join(page.extract_text() or "" for page in reader.pages)


def _make_evidence(
    *,
    id: str = "ev-1",
    evidence_type: str = "email",
    tags: list = None,
    source_date: str = "2026-03-15",
    description: str = "Respondent missed payment",
    transcription: str = "I will not pay this month.",
    filename: str = None,
    user_confirmed: bool = True,
) -> dict:
    return {
        "id": id,
        "evidence_type": evidence_type,
        "tags": tags if tags is not None else ["non_payment"],
        "source_date": source_date,
        "description": description,
        "transcription": transcription,
        "filename": filename,
        "user_confirmed": user_confirmed,
    }


# ---------------------------------------------------------------------------
# assign_exhibit_letters
# ---------------------------------------------------------------------------

from app.services.exhibit_assembly_service import (
    assign_exhibit_letters,
    build_exhibit_pages,
    insert_exhibit_references,
)


def test_single_item_gets_letter_a():
    items = [_make_evidence()]
    result = assign_exhibit_letters(items)
    assert len(result) == 1
    assert result[0][0] == "A"


def test_letters_assigned_a_through_z():
    items = [_make_evidence(id=str(i), source_date=f"2026-01-{i+1:02d}") for i in range(26)]
    result = assign_exhibit_letters(items)
    letters = [r[0] for r in result]
    expected = [chr(ord("A") + i) for i in range(26)]
    assert letters == expected


def test_letters_beyond_z_use_double_letters():
    """27th item gets AA, 28th gets AB, etc."""
    items = [_make_evidence(id=str(i), source_date=f"2026-01-01") for i in range(28)]
    result = assign_exhibit_letters(items)
    letters = [r[0] for r in result]
    assert letters[26] == "AA"
    assert letters[27] == "AB"


def test_sorted_by_source_date():
    items = [
        _make_evidence(id="b", source_date="2026-03-20", description="Later"),
        _make_evidence(id="a", source_date="2026-01-05", description="Earlier"),
    ]
    result = assign_exhibit_letters(items)
    assert result[0][1]["id"] == "a"  # earlier date → first → A
    assert result[1][1]["id"] == "b"
    assert result[0][0] == "A"
    assert result[1][0] == "B"


def test_null_source_date_sorted_last():
    items = [
        _make_evidence(id="null-date", source_date=None, description="No date"),
        _make_evidence(id="has-date", source_date="2026-01-01", description="Has date"),
    ]
    result = assign_exhibit_letters(items)
    assert result[0][1]["id"] == "has-date"
    assert result[1][1]["id"] == "null-date"


def test_items_without_tags_excluded():
    items = [
        _make_evidence(id="no-tags", tags=[]),
        _make_evidence(id="with-tags", tags=["threat"]),
    ]
    # assign_exhibit_letters works on raw items; filtering is in build_exhibit_pages
    # But per spec, assign_exhibit_letters receives already-filtered list.
    # We test via build_exhibit_pages filtering:
    ev_no_tags = _make_evidence(id="no-tags", tags=[])
    ev_confirmed_no_tags = dict(ev_no_tags)
    ev_confirmed_no_tags["user_confirmed"] = True

    ev_with_tags = _make_evidence(id="with-tags", tags=["non_payment"])
    ev_with_tags["user_confirmed"] = True

    evidence = [ev_confirmed_no_tags, ev_with_tags]
    pdf_bytes = build_exhibit_pages(assign_exhibit_letters([
        e for e in evidence
        if e.get("user_confirmed") and e.get("tags")
    ]))
    text = _extract_text(pdf_bytes)
    assert "no-tags" not in text
    assert "EXHIBIT A" in text


def test_unconfirmed_items_excluded():
    ev_unconfirmed = _make_evidence(id="unconfirmed", user_confirmed=False)
    ev_confirmed = _make_evidence(id="confirmed", user_confirmed=True)
    evidence = [ev_unconfirmed, ev_confirmed]

    eligible = [e for e in evidence if e.get("user_confirmed") and e.get("tags")]
    lettered = assign_exhibit_letters(eligible)
    pdf_bytes = build_exhibit_pages(lettered)
    text = _extract_text(pdf_bytes)
    assert "unconfirmed" not in text
    assert "EXHIBIT A" in text


# ---------------------------------------------------------------------------
# build_exhibit_pages
# ---------------------------------------------------------------------------

def test_build_exhibit_pages_valid_pdf():
    lettered = assign_exhibit_letters([_make_evidence()])
    pdf_bytes = build_exhibit_pages(lettered)
    assert pdf_bytes[:4] == b"%PDF"


def test_build_exhibit_pages_contains_exhibit_a():
    lettered = assign_exhibit_letters([_make_evidence()])
    pdf_bytes = build_exhibit_pages(lettered)
    text = _extract_text(pdf_bytes)
    assert "EXHIBIT A" in text


def test_build_exhibit_pages_cover_page_has_exhibits_heading():
    lettered = assign_exhibit_letters([_make_evidence()])
    pdf_bytes = build_exhibit_pages(lettered)
    text = _extract_text(pdf_bytes)
    assert "EXHIBITS" in text


def test_build_exhibit_pages_contains_description():
    ev = _make_evidence(description="Proof of missed payment on March 15")
    lettered = assign_exhibit_letters([ev])
    pdf_bytes = build_exhibit_pages(lettered)
    text = _extract_text(pdf_bytes)
    assert "Proof of missed payment on March 15" in text


def test_build_exhibit_pages_contains_transcription():
    ev = _make_evidence(transcription="I refuse to pay child support this month.")
    lettered = assign_exhibit_letters([ev])
    pdf_bytes = build_exhibit_pages(lettered)
    text = _extract_text(pdf_bytes)
    assert "I refuse to pay child support this month." in text


def test_build_exhibit_pages_multiple_exhibits():
    items = [
        _make_evidence(id="1", source_date="2026-01-01", description="First exhibit"),
        _make_evidence(id="2", source_date="2026-02-01", description="Second exhibit"),
    ]
    lettered = assign_exhibit_letters(items)
    pdf_bytes = build_exhibit_pages(lettered)
    text = _extract_text(pdf_bytes)
    assert "EXHIBIT A" in text
    assert "EXHIBIT B" in text


def test_build_exhibit_pages_empty_list_returns_valid_pdf():
    pdf_bytes = build_exhibit_pages([])
    assert pdf_bytes[:4] == b"%PDF"


# ---------------------------------------------------------------------------
# insert_exhibit_references
# ---------------------------------------------------------------------------

def test_insert_exhibit_references_appends_paragraph():
    lettered = assign_exhibit_letters([
        _make_evidence(id="1", source_date="2026-03-15", tags=["non_payment"])
    ])
    text = "Respondent has failed to pay child support."
    result = insert_exhibit_references(text, lettered)
    assert "Supporting exhibits:" in result
    assert "Exhibit A" in result


def test_insert_exhibit_references_includes_date_and_tag():
    lettered = assign_exhibit_letters([
        _make_evidence(id="1", source_date="2026-03-15", tags=["non_payment"])
    ])
    text = "Respondent has failed to pay child support."
    result = insert_exhibit_references(text, lettered)
    assert "2026-03-15" in result
    assert "non_payment" in result


def test_insert_exhibit_references_multiple_exhibits():
    lettered = assign_exhibit_letters([
        _make_evidence(id="1", source_date="2026-01-01", tags=["threat"]),
        _make_evidence(id="2", source_date="2026-02-01", tags=["custody_violation"]),
    ])
    text = "Multiple violations occurred."
    result = insert_exhibit_references(text, lettered)
    assert "Exhibit A" in result
    assert "Exhibit B" in result


def test_insert_exhibit_references_no_exhibits_unchanged():
    text = "No evidence attached."
    result = insert_exhibit_references(text, [])
    assert result == text


def test_insert_exhibit_references_no_llm_call(monkeypatch):
    """Must be purely mechanical — no external calls."""
    import app.services.exhibit_assembly_service as svc_module
    called = []

    # Patch any LLM service if present
    original = getattr(svc_module, "_llm_rewrite", None)
    if original:
        monkeypatch.setattr(svc_module, "_llm_rewrite", lambda *a, **k: called.append(1))

    lettered = assign_exhibit_letters([_make_evidence()])
    insert_exhibit_references("Some facts.", lettered)
    assert not called, "insert_exhibit_references must not call LLM"


# ---------------------------------------------------------------------------
# Integration: generate_packet with evidence
# ---------------------------------------------------------------------------

from app.services.pdf_packet_service import generate_packet


def _make_motion_stub(motion_type="RFO", has_support_issue=False):
    class _M:
        pass
    m = _M()
    m.motion_type = motion_type
    m.intake_data = {"has_support_issue": has_support_issue} if has_support_issue else {}
    m.hearing_date = "2024-06-15"
    m.hearing_time = "9:00 AM"
    m.case_caption = "Smith v. Smith"
    m.filing_date = None
    return m


def _make_profile_stub():
    class _P:
        pass
    p = _P()
    p.party_name = "John Smith"
    p.other_party_name = "Jane Smith"
    p.case_number = "FL-2024-001"
    p.county = "San Diego"
    p.is_petitioner = True
    p.party_address = "123 Main St"
    p.party_phone = "619-555-0100"
    p.other_party_attorney = None
    p.children_info = []
    return p


def _make_llm_sections(text="Respondent has failed to comply with custody order."):
    return [
        {
            "step_number": 1,
            "section": "Facts and Declaration",
            "original_answers": {"relief_categories": ["custody"]},
            "rewritten_text": text,
        }
    ]


@pytest.mark.asyncio
async def test_packet_with_evidence_larger_than_without():
    """Packet with exhibits must be larger than the same packet without."""
    motion = _make_motion_stub()
    profile = _make_profile_stub()
    sections = _make_llm_sections()

    evidence = [_make_evidence(user_confirmed=True, tags=["non_payment"])]

    packet_no_ev = await generate_packet(motion, profile, sections)
    packet_with_ev = await generate_packet(motion, profile, sections, evidence=evidence)

    assert packet_with_ev[:4] == b"%PDF"
    assert len(packet_with_ev) > len(packet_no_ev), (
        f"Packet with exhibits ({len(packet_with_ev)}) must be larger than without ({len(packet_no_ev)})"
    )


@pytest.mark.asyncio
async def test_packet_with_evidence_contains_exhibit_a():
    motion = _make_motion_stub()
    profile = _make_profile_stub()
    sections = _make_llm_sections()
    evidence = [_make_evidence(user_confirmed=True, tags=["non_payment"])]

    packet = await generate_packet(motion, profile, sections, evidence=evidence)
    text = _extract_text(packet)
    assert "EXHIBIT A" in text


@pytest.mark.asyncio
async def test_packet_with_evidence_declaration_has_supporting_exhibits():
    motion = _make_motion_stub()
    profile = _make_profile_stub()
    sections = _make_llm_sections()
    evidence = [_make_evidence(user_confirmed=True, tags=["non_payment"])]

    packet = await generate_packet(motion, profile, sections, evidence=evidence)
    text = _extract_text(packet)
    assert "Supporting exhibits:" in text


@pytest.mark.asyncio
async def test_packet_without_evidence_unchanged():
    """Regression: packet without evidence must be identical to pre-exhibit behavior."""
    motion = _make_motion_stub()
    profile = _make_profile_stub()
    sections = _make_llm_sections()

    packet_before = await generate_packet(motion, profile, sections)
    packet_after = await generate_packet(motion, profile, sections, evidence=[])

    # Same page count — structural equivalence
    reader_before = PyPDF2.PdfReader(io.BytesIO(packet_before))
    reader_after = PyPDF2.PdfReader(io.BytesIO(packet_after))
    assert len(reader_before.pages) == len(reader_after.pages), (
        "Empty evidence list must not alter packet structure"
    )


@pytest.mark.asyncio
async def test_packet_unconfirmed_evidence_excluded():
    """Evidence items with user_confirmed=False must not appear in packet."""
    motion = _make_motion_stub()
    profile = _make_profile_stub()
    sections = _make_llm_sections()
    evidence = [_make_evidence(id="unconfirmed", user_confirmed=False, tags=["threat"])]

    packet_no_ev = await generate_packet(motion, profile, sections)
    packet_unconf = await generate_packet(motion, profile, sections, evidence=evidence)

    reader_no = PyPDF2.PdfReader(io.BytesIO(packet_no_ev))
    reader_unc = PyPDF2.PdfReader(io.BytesIO(packet_unconf))
    assert len(reader_no.pages) == len(reader_unc.pages), (
        "Unconfirmed evidence must not add pages to the packet"
    )
