"""
API endpoints for San Diego violation filings
"""
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.services.fact_gate import GateContext, run_fact_gate
from app.services.violation_intake_steps import build_wizard_steps
from app.services.violation_service import ViolationFilingService
from app.api.v1.endpoints.auth import get_current_user
from app.models.user import User, Profile
from app.models.motion import Motion, MotionType
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/violations", tags=["violations"])

# Pydantic models for request/response
class ViolationIntakeRequest(BaseModel):
    """Request model for violation intake data"""
    violationType: str = Field(..., description="Type of court order violated")
    urgency: bool = Field(default=False, description="Is this an emergency?")
    violationDates: list[str] = Field(..., description="Dates of violations")
    violationDescription: str = Field(..., description="Detailed description")
    evidence: list[str] = Field(default=[], description="Types of evidence available")
    attemptedResolution: bool = Field(default=False)
    resolutionDescription: Optional[str] = None
    priorViolations: bool = Field(default=False)
    priorViolationsDescription: Optional[str] = None
    requestedRelief: list[str] = Field(..., description="What relief is requested")

class ViolationFilingResponse(BaseModel):
    """Response model for violation filing"""
    success: bool
    track: str
    trackName: str
    timeline: str
    forms: list[Dict[str, Any]]
    declaration: str
    courthouse: Dict[str, str]
    instructions: list[str]
    filingFee: str
    serviceRequirements: Dict[str, Any]
    corrections: list[Dict[str, Any]] = []
    error: Optional[str] = None

# Initialize service
violation_service = ViolationFilingService()


def _declaration_gate_context(
    intake: Dict[str, Any], profile_data: Optional[Dict[str, Any]]
) -> GateContext:
    """Ground truth for gating a generated declaration (findings L4, L7, L15)."""
    profile_data = profile_data or {}
    return GateContext(
        motion_kind="declaration",
        section_name="declaration",
        party_name=profile_data.get("party_name") or "",
        other_party_name=profile_data.get("other_party_name") or "",
        is_petitioner=bool(profile_data.get("is_petitioner", True)),
        case_number=profile_data.get("case_number") or "",
        county=profile_data.get("county") or "",
        children=profile_data.get("children_info") or [],
        intake_values=intake,
    )

@router.post("/process", response_model=ViolationFilingResponse)
async def process_violation_filing(
    intake_data: ViolationIntakeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Process a violation filing based on intake data

    Returns:
    - Filing track (emergency, regular, contempt)
    - Required forms list
    - Generated declaration
    - Filing instructions
    """
    try:
        # Get user profile for courthouse determination.
        # Explicit query — lazy-loading current_user.profile raises
        # MissingGreenlet under the async session.
        result = await db.execute(
            select(Profile).where(Profile.user_id == current_user.id)
        )
        profile = result.scalar_one_or_none()
        profile_data = None
        if profile:
            # Full party context — under-passing here left the fact gate
            # unable to fill "[PETITIONER'S FULL LEGAL NAME]" placeholders (L15)
            profile_data = {
                "city": profile.city,
                "zipCode": profile.zip_code,
                "county": profile.county,
                "party_name": profile.party_name,
                "other_party_name": profile.other_party_name,
                "is_petitioner": profile.is_petitioner,
                "case_number": profile.case_number,
                "children_info": profile.children_info,
            }

        # Process the violation filing
        result = await violation_service.process_violation_filing(
            user_id=str(current_user.id),
            intake_data=intake_data.dict(),
            profile_data=profile_data
        )

        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Failed to process violation filing")
            )

        # Gate the generated declaration against user-entered facts
        gated = run_fact_gate(
            result["declaration"],
            _declaration_gate_context(intake_data.dict(), profile_data),
        )
        result["declaration"] = gated.text
        result["corrections"] = [c.as_dict() for c in gated.corrections]

        # Save to database as a motion
        motion = Motion(
            user_id=current_user.id,
            motion_type=MotionType.VIOLATION,
            title=f"Violation Filing - {intake_data.violationType}",
            description=intake_data.violationDescription[:500],
            filing_track=result["track"],
            courthouse=result["courthouse"].get("name"),
            status="draft",
            intake_data=intake_data.dict(),
            generated_text=result["declaration"],
            fact_check={"version": 1, "corrections": result["corrections"]}
        )
        db.add(motion)
        await db.commit()

        logger.info(f"Processed violation filing for user {current_user.id}, track: {result['track']}")

        return ViolationFilingResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing violation filing: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process violation filing"
        )

@router.get("/tracks")
async def get_filing_tracks(
    current_user: User = Depends(get_current_user)
):
    """Get available filing tracks and their descriptions"""
    config = violation_service.config.get("violationFiling", {})
    tracks = config.get("tracks", [])

    return {
        "tracks": tracks,
        "courthouses": config.get("courthouses", [])
    }

@router.get("/intake-questions")
async def get_intake_questions(
    current_user: User = Depends(get_current_user)
):
    """Get the violation intake questions as the wizard steps the frontend renders"""
    config = violation_service.config.get("violationFiling", {})
    questions = config.get("intakeQuestions", {})

    return {"questions": build_wizard_steps(questions)}

@router.get("/forms/{track}")
async def get_track_forms(
    track: str,
    current_user: User = Depends(get_current_user)
):
    """Get required forms for a specific filing track"""
    if track not in ["emergency", "regular", "contempt"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid track. Must be 'emergency', 'regular', or 'contempt'"
        )

    forms = violation_service.get_required_forms(track)

    return {
        "track": track,
        "forms": forms
    }

@router.post("/generate-declaration")
async def generate_declaration(
    intake_data: ViolationIntakeRequest,
    current_user: User = Depends(get_current_user)
):
    """Generate a declaration based on intake data"""
    try:
        # Generate basic declaration
        declaration_text = violation_service.prepare_declaration(intake_data.dict())

        # Enhance with LLM
        enhanced = await violation_service.llm_service.enhance_declaration(
            declaration_text,
            formal=True,
            legal_tone=True
        )

        # Gate against user-entered facts (no profile on this endpoint)
        gated = run_fact_gate(
            enhanced.get("enhanced_text", declaration_text),
            _declaration_gate_context(intake_data.dict(), None),
        )

        return {
            "success": True,
            "declaration": gated.text,
            "corrections": [c.as_dict() for c in gated.corrections],
            "originalLength": len(declaration_text),
            "enhancedLength": len(gated.text)
        }

    except Exception as e:
        logger.error(f"Error generating declaration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )