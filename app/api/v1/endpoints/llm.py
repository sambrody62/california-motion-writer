"""
LLM integration endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging
import uuid

from app.models.user import User
from app.models.motion import Motion, MotionDraft
from app.models.profile import Profile
from app.api.v1.endpoints.auth import get_current_user
from app.core.database import get_db
from app.services.llm_service import llm_service

router = APIRouter()
logger = logging.getLogger(__name__)

class RewriteRequest(BaseModel):
    motion_type: str  # 'RFO' or 'RESPONSE'
    section: str  # 'facts', 'relief', 'best_interests', etc.
    user_input: str
    context: Optional[dict] = {}

class RewriteResponse(BaseModel):
    original: str
    rewritten: str
    tokens_used: int
    success: bool
    error: Optional[str] = None

class ProcessMotionRequest(BaseModel):
    motion_id: str

class ProcessMotionResponse(BaseModel):
    motion_id: str
    success: bool
    sections_processed: int
    total_tokens: int
    errors: List[str] = []

class DeclarationRequest(BaseModel):
    narrative: str
    declarant_name: str

class BestInterestsRequest(BaseModel):
    custody_request: str
    children_info: List[Dict[str, Any]]

@router.post("/rewrite", response_model=RewriteResponse)
async def rewrite_text(
    request: RewriteRequest,
    current_user: User = Depends(get_current_user)
):
    """Rewrite text using Vertex AI"""
    logger.info(f"Rewrite request for {request.motion_type} - {request.section}")
    
    try:
        # Call LLM service
        result = await llm_service.rewrite_rfo_section(
            section_name=request.section,
            user_answers={"user_input": request.user_input},
            context=request.context
        )
        
        return RewriteResponse(
            original=request.user_input,
            rewritten=result.get("rewritten_text", ""),
            tokens_used=result.get("tokens_used", 0),
            success=result.get("success", False),
            error=result.get("error")
        )
    except Exception as e:
        logger.error(f"Error in rewrite: {str(e)}")
        return RewriteResponse(
            original=request.user_input,
            rewritten="",
            tokens_used=0,
            success=False,
            error=str(e)
        )

@router.post("/process-motion", response_model=ProcessMotionResponse)
async def process_complete_motion(
    request: ProcessMotionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Process all sections of a motion through LLM"""
    try:
        # Get motion and verify ownership
        motion_result = await db.execute(
            select(Motion)
            .where(Motion.id == uuid.UUID(request.motion_id))
            .where(Motion.user_id == current_user.id)
        )
        motion = motion_result.scalar_one_or_none()
        
        if not motion:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Motion not found"
            )
        
        # Get user profile
        profile_result = await db.execute(
            select(Profile)
            .where(Profile.user_id == current_user.id)
        )
        profile = profile_result.scalar_one_or_none()
        
        profile_data = {}
        if profile:
            profile_data = {
                "is_petitioner": profile.is_petitioner,
                "county": profile.county,
                "case_number": profile.case_number,
                "party_name": profile.party_name,
                "other_party_name": profile.other_party_name,
                "children_info": profile.children_info
            }
        
        # Get all drafts for the motion
        drafts_result = await db.execute(
            select(MotionDraft)
            .where(MotionDraft.motion_id == motion.id)
            .order_by(MotionDraft.step_number)
        )
        drafts = drafts_result.scalars().all()
        
        if not drafts:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No draft sections found for this motion"
            )
        
        # Prepare draft data
        draft_data = [
            {
                "step_number": draft.step_number,
                "step_name": draft.step_name,
                "question_data": draft.question_data
            }
            for draft in drafts
        ]
        
        # Process through LLM
        result = await llm_service.process_complete_motion(
            motion_type=motion.motion_type,
            all_drafts=draft_data,
            profile_data=profile_data
        )
        
        # Update drafts with LLM output
        errors = []
        sections_processed = 0
        
        for section in result.get("sections", []):
            if section.get("success"):
                # Find and update the corresponding draft
                for draft in drafts:
                    if draft.step_number == section.get("step_number"):
                        draft.llm_output = section.get("rewritten_text")
                        draft.llm_model = result.get("model")
                        draft.llm_tokens_used = section.get("tokens_used", 0)
                        draft.is_complete = True
                        sections_processed += 1
                        break
            else:
                errors.append(f"Section {section.get('section')}: {section.get('error')}")
        
        # Update motion status if all sections processed
        if sections_processed == len(drafts):
            motion.status = "ready_for_review"
        
        await db.commit()
        
        return ProcessMotionResponse(
            motion_id=request.motion_id,
            success=result.get("success", False),
            sections_processed=sections_processed,
            total_tokens=result.get("total_tokens", 0),
            errors=errors
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing motion: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing motion: {str(e)}"
        )

@router.post("/rewrite-declaration")
async def rewrite_declaration(
    request: DeclarationRequest,
    current_user: User = Depends(get_current_user)
):
    """Convert narrative to formal declaration"""
    try:
        result = await llm_service.rewrite_declaration(
            narrative=request.narrative,
            declarant_name=request.declarant_name
        )
        
        return {
            "success": result.get("success"),
            "declaration": result.get("rewritten_text"),
            "tokens_used": result.get("tokens_used"),
            "error": result.get("error")
        }
    except Exception as e:
        logger.error(f"Error rewriting declaration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/enhance-best-interests")
async def enhance_best_interests(
    request: BestInterestsRequest,
    current_user: User = Depends(get_current_user)
):
    """Enhance custody request with best interests factors"""
    try:
        result = await llm_service.enhance_best_interests(
            custody_request=request.custody_request,
            children_info=request.children_info
        )
        
        return {
            "success": result.get("success"),
            "enhanced_text": result.get("enhanced_text"),
            "tokens_used": result.get("tokens_used"),
            "error": result.get("error")
        }
    except Exception as e:
        logger.error(f"Error enhancing best interests: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )