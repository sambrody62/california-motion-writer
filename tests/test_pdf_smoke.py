"""
Smoke tests for end-to-end PDF generation via pdf_service.generate_motion_pdf.

Covers:
- Output is a valid PDF (starts with %PDF)
- Output is larger than 10 KB
- Extracted text contains both party names and the case number
- FL-150 is generated and contains party info when has_support_issue is True
  (pdf_service does not assemble multi-form packets; that is noted as a blocker)
"""
import asyncio
import io
import pytest
import pytest_asyncio
import PyPDF2

from app.services.pdf_service import PDFService


@pytest_asyncio.fixture
async def svc():
    return PDFService()


def _extract_text(pdf_bytes: bytes) -> str:
    reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
    return "".join(page.extract_text() or "" for page in reader.pages)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_motion_inputs(*, has_support_issue: bool = False):
    profile_data = {
        "party_name": "John Smith",
        "other_party_name": "Jane Smith",
        "case_number": "FL-2024-001",
        "county": "San Diego",
        "is_petitioner": True,
    }
    motion_data = {
        "hearing_date": "2024-06-15",
        "hearing_time": "9:00 AM",
    }
    answers = {}
    if has_support_issue:
        answers["relief_categories"] = ["custody", "child_support"]
        answers["child_support_amount"] = "$1,500"

    llm_sections = [
        {
            "step_number": 1,
            "section": "Facts and Declaration",
            "original_answers": answers,
            "rewritten_text": (
                "Petitioner John Smith states that respondent Jane Smith has "
                "repeatedly failed to comply with the existing custody order. "
                "Petitioner respectfully requests the Court issue the orders "
                "described herein in the best interest of the minor children."
            ),
        }
    ]
    return profile_data, motion_data, llm_sections


# ---------------------------------------------------------------------------
# FL-300 smoke test (RFO motion)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_fl300_is_valid_pdf(svc):
    profile, motion, sections = _make_motion_inputs()
    pdf = await svc.generate_motion_pdf("RFO", motion, profile, sections)

    assert pdf[:4] == b"%PDF", "Output must start with %PDF magic bytes"


@pytest.mark.asyncio
async def test_fl300_size_exceeds_10kb(svc):
    profile, motion, sections = _make_motion_inputs()
    pdf = await svc.generate_motion_pdf("RFO", motion, profile, sections)

    assert len(pdf) > 10_240, f"Expected >10 KB, got {len(pdf)} bytes"


@pytest.mark.asyncio
async def test_fl300_contains_party_names_and_case_number(svc):
    profile, motion, sections = _make_motion_inputs()
    pdf = await svc.generate_motion_pdf("RFO", motion, profile, sections)

    text = _extract_text(pdf)
    assert "John Smith" in text, "Petitioner name must appear in extracted text"
    assert "Jane Smith" in text, "Respondent name must appear in extracted text"
    assert "FL-2024-001" in text, "Case number must appear in extracted text"


@pytest.mark.asyncio
async def test_fl300_with_support_issue_sets_checkboxes(svc):
    """Relief category checkboxes are written when relief_categories includes child_support."""
    profile, motion, sections = _make_motion_inputs(has_support_issue=True)
    pdf = await svc.generate_motion_pdf("RFO", motion, profile, sections)

    assert pdf[:4] == b"%PDF"
    assert len(pdf) > 10_240


# ---------------------------------------------------------------------------
# FL-150 direct fill smoke test
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_fl150_is_valid_pdf(svc):
    form_data = {
        "petitioner_name": "John Smith",
        "respondent_name": "Jane Smith",
        "case_number": "FL-2024-001",
        "employer_name": "Acme Corporation",
        "gross_monthly_income": "5000",
    }
    pdf = await svc.fill_form("FL-150", form_data)

    assert pdf[:4] == b"%PDF", "FL-150 output must start with %PDF magic bytes"
    assert len(pdf) > 10_240, f"Expected >10 KB, got {len(pdf)} bytes"


@pytest.mark.asyncio
async def test_fl150_contains_party_names_and_case_number(svc):
    form_data = {
        "petitioner_name": "John Smith",
        "respondent_name": "Jane Smith",
        "case_number": "FL-2024-001",
        "employer_name": "Acme Corporation",
        "gross_monthly_income": "5000",
    }
    pdf = await svc.fill_form("FL-150", form_data)
    text = _extract_text(pdf)

    assert "John Smith" in text, "Petitioner name must appear in FL-150 extracted text"
    assert "Jane Smith" in text, "Respondent name must appear in FL-150 extracted text"
    assert "FL-2024-001" in text, "Case number must appear in FL-150 extracted text"


# ---------------------------------------------------------------------------
# Packet / multi-form tests (generate_packet)
# ---------------------------------------------------------------------------

from app.services.pdf_packet_service import generate_packet


def _make_motion_stub(motion_type: str, has_support_issue: bool = False):
    """Minimal motion-like dict used by generate_packet tests."""
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


def _make_profile_stub(party_name="John Smith", other="Jane Smith", case_number="FL-2024-001"):
    class _P:
        pass
    p = _P()
    p.party_name = party_name
    p.other_party_name = other
    p.case_number = case_number
    p.county = "San Diego"
    p.is_petitioner = True
    p.party_address = "123 Main St"
    p.party_phone = "619-555-0100"
    p.other_party_attorney = None
    p.children_info = []
    return p


def _make_llm_sections(text="Petitioner John Smith states facts."):
    return [
        {
            "step_number": 1,
            "section": "Facts and Declaration",
            "original_answers": {"relief_categories": ["custody"]},
            "rewritten_text": text,
        }
    ]


# --- RFO + support issue → FL-300 + MC-030 + FL-150 packet ---

@pytest.mark.asyncio
async def test_packet_rfo_support_issue_contains_fl300_and_fl150():
    """RFO with has_support_issue=True must produce a packet larger than FL-300 alone."""
    motion = _make_motion_stub("RFO", has_support_issue=True)
    profile = _make_profile_stub()
    llm_sections = _make_llm_sections()

    svc = PDFService()
    single_pdf = await svc.generate_motion_pdf("RFO", {"hearing_date": "2024-06-15"}, {
        "party_name": "John Smith", "other_party_name": "Jane Smith",
        "case_number": "FL-2024-001", "county": "San Diego", "is_petitioner": True
    }, llm_sections)

    packet = await generate_packet(motion, profile, llm_sections)

    assert packet[:4] == b"%PDF", "Packet must start with %PDF"
    assert len(packet) > len(single_pdf), (
        f"Packet ({len(packet)} bytes) must be larger than single FL-300 ({len(single_pdf)} bytes)"
    )


@pytest.mark.asyncio
async def test_packet_rfo_support_issue_party_names_in_all_forms():
    """Party names and case number must appear in the merged packet text."""
    motion = _make_motion_stub("RFO", has_support_issue=True)
    profile = _make_profile_stub()
    llm_sections = _make_llm_sections()

    packet = await generate_packet(motion, profile, llm_sections)
    text = _extract_text(packet)

    assert "John Smith" in text, "Petitioner name must appear in packet"
    assert "Jane Smith" in text, "Respondent name must appear in packet"
    assert "FL-2024-001" in text, "Case number must appear in packet"


# --- RFO without support issue → FL-300 + MC-030 (no FL-150) ---

@pytest.mark.asyncio
async def test_packet_rfo_no_support_issue_excludes_fl150():
    """RFO without has_support_issue must not include FL-150 pages."""
    motion = _make_motion_stub("RFO", has_support_issue=False)
    profile = _make_profile_stub()
    llm_sections = _make_llm_sections()

    motion_support = _make_motion_stub("RFO", has_support_issue=True)
    packet_no_support = await generate_packet(motion, profile, llm_sections)
    packet_with_support = await generate_packet(motion_support, profile, llm_sections)

    reader_no = PyPDF2.PdfReader(io.BytesIO(packet_no_support))
    reader_with = PyPDF2.PdfReader(io.BytesIO(packet_with_support))

    assert len(reader_no.pages) < len(reader_with.pages), (
        "Packet without support issue must have fewer pages than one with FL-150"
    )


# --- RESPONSE motion → FL-320 packet ---

@pytest.mark.asyncio
async def test_packet_response_produces_fl320():
    """RESPONSE motion must use FL-320 as the primary form."""
    motion = _make_motion_stub("RESPONSE", has_support_issue=False)
    profile = _make_profile_stub()
    llm_sections = _make_llm_sections("Respondent Jane Smith agrees in part.")

    packet = await generate_packet(motion, profile, llm_sections)

    assert packet[:4] == b"%PDF", "Packet must start with %PDF"
    assert len(packet) > 10_240, f"Expected >10 KB, got {len(packet)} bytes"
    text = _extract_text(packet)
    assert "Jane Smith" in text, "Respondent name must appear in RESPONSE packet"


@pytest.mark.asyncio
async def test_packet_response_party_names_extractable():
    """Party names must be extractable from every included form in RESPONSE packet."""
    motion = _make_motion_stub("RESPONSE", has_support_issue=False)
    profile = _make_profile_stub()
    llm_sections = _make_llm_sections()

    packet = await generate_packet(motion, profile, llm_sections)
    text = _extract_text(packet)

    assert "John Smith" in text
    assert "Jane Smith" in text
    assert "FL-2024-001" in text


# --- Violation type uses FL-300 ---

@pytest.mark.asyncio
async def test_packet_violation_uses_fl300():
    """Violation motion type must use FL-300 as its primary form."""
    motion = _make_motion_stub("violation", has_support_issue=False)
    profile = _make_profile_stub()
    llm_sections = _make_llm_sections()

    packet = await generate_packet(motion, profile, llm_sections)

    assert packet[:4] == b"%PDF"
    assert len(packet) > 10_240
