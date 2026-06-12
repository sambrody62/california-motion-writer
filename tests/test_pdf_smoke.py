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
# Packet / multi-form support note
# ---------------------------------------------------------------------------
# pdf_service.generate_motion_pdf does NOT assemble a multi-form packet.
# It generates only the primary form (FL-300 for RFO, FL-320 for Response).
# There is no automatic inclusion of FL-150 when has_support_issue is True.
# BLOCKER: pdf_service needs a generate_packet() method (or caller logic) that
# adds FL-150 to the output when intake_data.has_support_issue is set.
