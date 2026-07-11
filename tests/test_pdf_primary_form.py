"""
Primary-form selection for PDF packets.

Regression for the 2026-07-11 real-LLM browser finding L6: guided FL-300
motions downloaded with FL-320 "Responsive Declaration" as pages 1-2 because
pdf_packet_service's FL-300 type set omitted "fl-300" (documents.py carried
its own, correct set that only the async path used).
"""
import io
from pathlib import Path

import pytest
import PyPDF2

from app.services.pdf_packet_service import generate_packet

# Present ONLY in the FL-320 blank among the forms a packet can contain
# (FL-300, FL-320, FL-150, MC-030) — proven by test_fl320_marker_is_distinctive.
# NOTE: "RESPONSIVE DECLARATION" is NOT distinctive: the FL-300 blank's notice
# text references form FL-320 by that title.
FL320_MARKER = "CONSENT TO THE ORDER REQUESTED"

_FORMS_ROOT = Path(__file__).parent.parent / "forms"


def _extract_text(pdf_bytes: bytes) -> str:
    reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
    return "".join(page.extract_text() or "" for page in reader.pages)


def _blank_form_text(relative_path: str) -> str:
    with open(_FORMS_ROOT / relative_path, "rb") as fh:
        reader = PyPDF2.PdfReader(fh)
        return "".join(page.extract_text() or "" for page in reader.pages)


def _make_motion_stub(motion_type: str):
    class _M:
        pass
    m = _M()
    m.motion_type = motion_type
    m.intake_data = {}
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


def _make_llm_sections():
    return [
        {
            "step_number": 1,
            "section": "Facts and Declaration",
            "original_answers": {"relief_categories": ["custody"]},
            "rewritten_text": "Petitioner John Smith states facts.",
        }
    ]


def test_fl320_marker_is_distinctive():
    """The marker must appear in the FL-320 blank and in no other packet form —
    otherwise the packet assertions below prove nothing."""
    assert FL320_MARKER in _blank_form_text("FL-320.pdf").upper()
    assert FL320_MARKER not in _blank_form_text("FL-300.pdf").upper()
    assert FL320_MARKER not in _blank_form_text("FL-150.pdf").upper()
    assert FL320_MARKER not in _blank_form_text("san-diego-violation/mc030.pdf").upper()


@pytest.mark.parametrize(
    "motion_type,expected",
    [
        ("FL-300", "FL-300"),
        ("fl-300", "FL-300"),
        ("rfo", "FL-300"),
        ("violation", "FL-300"),
        ("RESPONSE", "FL-320"),
        ("FL-320", "FL-320"),
    ],
)
def test_primary_form_for(motion_type, expected):
    from app.services.pdf_packet_service import primary_form_for

    assert primary_form_for(motion_type) == expected


@pytest.mark.asyncio
async def test_packet_fl300_literal_type_has_no_fl320_pages():
    """Guided intake stores motion_type 'FL-300'; its packet must not lead with FL-320."""
    motion = _make_motion_stub("FL-300")
    packet = await generate_packet(motion, _make_profile_stub(), _make_llm_sections())

    assert packet[:4] == b"%PDF"
    assert FL320_MARKER not in _extract_text(packet).upper()


@pytest.mark.asyncio
async def test_packet_response_type_has_fl320_pages():
    """Positive control: the marker does appear when FL-320 is the primary form."""
    motion = _make_motion_stub("RESPONSE")
    packet = await generate_packet(motion, _make_profile_stub(), _make_llm_sections())

    assert FL320_MARKER in _extract_text(packet).upper()
