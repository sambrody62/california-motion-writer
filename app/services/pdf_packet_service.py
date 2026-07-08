"""
PDF Packet Service — assembles multi-form PDF packets for California court motions.

Packet composition rules:
  RFO / violation types  → FL-300  [+ MC-030 when llm_sections present] [+ FL-150 when has_support_issue]
  RESPONSE               → FL-320  [+ MC-030 when llm_sections present] [+ FL-150 when has_support_issue]
  When evidence is provided, confirmed+tagged items are appended as lettered exhibits.
"""
from __future__ import annotations

import io
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable

import PyPDF2

from app.services.pdf_service import PDFService
from app.services.claim_citation_service import insert_claim_citations
from app.services.exhibit_assembly_service import assign_exhibit_letters
from app.services.exhibit_formatting import build_authentication_text, build_exhibit_packet

_pdf_svc = PDFService()

_FORMS_ROOT = Path(__file__).parent.parent.parent / "forms"
_MC030_PATH = _FORMS_ROOT / "san-diego-violation" / "mc030.pdf"
_FL150_PATH = _FORMS_ROOT / "FL-150.pdf"

# Motion types that use FL-300 as the primary form.
_FL300_TYPES = {"rfo", "violation"}


@runtime_checkable
class _MotionLike(Protocol):
    motion_type: str
    intake_data: Dict[str, Any]
    hearing_date: Any
    hearing_time: Any
    case_caption: Any
    filing_date: Any


@runtime_checkable
class _ProfileLike(Protocol):
    party_name: str
    other_party_name: str
    case_number: str
    county: str
    is_petitioner: bool
    party_address: Any
    party_phone: Any
    other_party_attorney: Any
    children_info: Any


def _primary_form(motion_type) -> str:
    """Return the primary form name for a motion type (str or enum)."""
    raw = motion_type.value if hasattr(motion_type, "value") else str(motion_type)
    return "FL-300" if raw.lower() in _FL300_TYPES else "FL-320"


def _has_declaration_text(llm_sections: List[Dict[str, Any]]) -> bool:
    return any(s.get("rewritten_text", "").strip() for s in llm_sections)


def _build_profile_data(profile: _ProfileLike) -> Dict[str, Any]:
    return {
        "is_petitioner": profile.is_petitioner,
        "county": profile.county,
        "case_number": profile.case_number,
        "party_name": profile.party_name,
        "other_party_name": profile.other_party_name,
        "party_address": getattr(profile, "party_address", ""),
        "party_phone": getattr(profile, "party_phone", ""),
        "other_party_attorney": getattr(profile, "other_party_attorney", None),
        "children_info": getattr(profile, "children_info", []) or [],
    }


def _build_motion_data(motion: _MotionLike) -> Dict[str, Any]:
    return {
        "motion_type": motion.motion_type,
        "case_caption": getattr(motion, "case_caption", ""),
        "filing_date": getattr(motion, "filing_date", None),
        "hearing_date": getattr(motion, "hearing_date", None),
        "hearing_time": getattr(motion, "hearing_time", None),
    }


async def _fill_mc030(profile: _ProfileLike, declaration_text: str) -> bytes:
    """Overlay party names + declaration body onto the MC-030 blank."""
    form_data = {
        "petitioner_name": profile.party_name,
        "respondent_name": profile.other_party_name,
        "case_number": profile.case_number,
        "declaration_text": declaration_text,
    }

    from app.services import pdf_text_utils as ptu

    overflow_lines: List[str] = []
    with open(_MC030_PATH, "rb") as fh:
        reader = PyPDF2.PdfReader(fh)
        writer = PyPDF2.PdfWriter()

        import reportlab.pdfgen.canvas as rl_canvas
        from reportlab.lib.pagesizes import letter

        for page_idx, page in enumerate(reader.pages):
            overlay_buf = io.BytesIO()
            c = rl_canvas.Canvas(overlay_buf, pagesize=letter)

            if page_idx == 0:
                # Party names block (top-right caption area)
                c.drawString(100, 680, f"Petitioner: {profile.party_name}")
                c.drawString(100, 662, f"Respondent: {profile.other_party_name}")
                c.drawString(400, 680, f"Case No.: {profile.case_number}")
                # Declaration body — overflow continues on attachment pages
                lines = ptu.wrap_text_accurate(declaration_text, width=468)
                overflow_lines = ptu.draw_lines_in_box(c, lines, x=72, y=580, height=460)

            c.save()
            overlay_buf.seek(0)

            overlay_reader = PyPDF2.PdfReader(overlay_buf)
            if overlay_reader.pages:
                page.merge_page(overlay_reader.pages[0])
            writer.add_page(page)

        if overflow_lines:
            attachment = ptu.build_continuation_pages(
                overflow_lines,
                caption="ATTACHMENT — Declaration (continued)",
                case_number=str(profile.case_number or ""),
            )
            for att_page in PyPDF2.PdfReader(io.BytesIO(attachment)).pages:
                writer.add_page(att_page)

    buf = io.BytesIO()
    writer.write(buf)
    buf.seek(0)
    return buf.read()


async def _fill_fl150(profile: _ProfileLike) -> bytes:
    """Fill FL-150 with party names and case number from profile."""
    form_data = {
        "petitioner_name": profile.party_name,
        "respondent_name": profile.other_party_name,
        "case_number": profile.case_number,
    }
    return await _pdf_svc.fill_form("FL-150", form_data)


def _merge_pdfs(parts: List[bytes]) -> bytes:
    """Merge a list of PDF byte strings into one using PdfWriter.append."""
    writer = PyPDF2.PdfWriter()
    for part in parts:
        reader = PyPDF2.PdfReader(io.BytesIO(part))
        for page in reader.pages:
            writer.add_page(page)
    buf = io.BytesIO()
    writer.write(buf)
    buf.seek(0)
    return buf.read()




async def generate_packet(
    motion: _MotionLike,
    profile: _ProfileLike,
    llm_sections: List[Dict[str, Any]],
    evidence: Optional[List[Dict[str, Any]]] = None,
) -> bytes:
    """Assemble a merged PDF packet for the given motion.

    Args:
        motion:       ORM Motion object (or duck-typed equivalent).
        profile:      ORM Profile object (or duck-typed equivalent).
        llm_sections: List of section dicts with 'rewritten_text' and 'original_answers'.
        evidence:     Optional list of evidence dicts (shared shape). Only items with
                      user_confirmed=True and at least one tag will be included as exhibits.

    Returns:
        Merged PDF as bytes.
    """
    # Filter evidence to confirmed+tagged items only.
    eligible = [
        e for e in (evidence or [])
        if e.get("user_confirmed") and e.get("tags")
    ]
    lettered = assign_exhibit_letters(eligible) if eligible else []

    # 1. Primary form
    primary_form = _primary_form(motion.motion_type)
    primary_bytes = await _pdf_svc.fill_form(primary_form, {
        "petitioner_name": profile.party_name,
        "respondent_name": profile.other_party_name,
        "case_number": profile.case_number,
        "court_name": "Superior Court of California",
        "court_address": f"County of {profile.county}",
        "attorney_for": "In Pro Per",
        "hearing_date": getattr(motion, "hearing_date", "") or "",
        "hearing_time": getattr(motion, "hearing_time", "") or "",
    })

    parts: List[bytes] = [primary_bytes]

    # 2. MC-030 declaration page when LLM text is present
    if _has_declaration_text(llm_sections):
        declaration_text = "\n\n".join(
            s["rewritten_text"] for s in llm_sections if s.get("rewritten_text", "").strip()
        )
        if lettered:
            # Inline citations first (falls back to unchanged text on any doubt),
            # then authenticate every exhibit under the declaration's perjury clause
            declaration_text = await insert_claim_citations(declaration_text, lettered)
            declaration_text = declaration_text + "\n\n" + build_authentication_text(lettered)
        mc030_bytes = await _fill_mc030(profile, declaration_text)
        parts.append(mc030_bytes)

    # 3. FL-150 when motion has a support issue
    intake = getattr(motion, "intake_data", None) or {}
    if intake.get("has_support_issue"):
        fl150_bytes = await _fill_fl150(profile)
        parts.append(fl150_bytes)

    # 4. Exhibit packet (index + caption headers + page stamps) appended last
    if lettered:
        caption = {
            "case_number": str(profile.case_number or ""),
            "party_name": profile.party_name,
            "other_party_name": profile.other_party_name,
        }
        parts.append(build_exhibit_packet(lettered, caption))

    return _merge_pdfs(parts)
