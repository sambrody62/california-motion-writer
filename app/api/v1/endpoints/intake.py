"""
Intake flow endpoints for guided Q&A
"""
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid

from app.core.database import get_db
from app.models.user import User
from app.models.motion import Motion, MotionDraft
from app.api.v1.endpoints.auth import get_current_user
from app.services.intake import intake_service

router = APIRouter()

class IntakeStepRequest(BaseModel):
    motion_id: str
    current_step: int
    answers: Dict[str, Any]

class IntakeStepResponse(BaseModel):
    step_number: int
    section: str
    title: str
    questions: List[Dict[str, Any]]
    progress: float
    is_final_step: bool
    required_attachments: Optional[List[str]] = None

class IntakeAnswerSubmit(BaseModel):
    motion_id: str
    step_number: int
    answers: Dict[str, Any]

class ValidationResponse(BaseModel):
    valid: bool
    errors: Dict[str, str] = {}
    next_step: Optional[IntakeStepResponse] = None

@router.get("/rfo/steps")
async def get_rfo_steps(
    current_user: User = Depends(get_current_user)
):
    """Get all RFO intake steps overview"""
    steps = intake_service.get_all_steps()
    return {
        "total_steps": len(steps),
        "steps": [
            {
                "step": step["step"],
                "section": step["section"],
                "title": step["title"],
                "conditional": "condition" in step
            }
            for step in steps
        ]
    }

@router.post("/rfo/start")
async def start_rfo_intake(
    motion_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Start RFO intake for a motion"""
    # Verify motion exists and belongs to user
    result = await db.execute(
        select(Motion)
        .where(Motion.id == uuid.UUID(motion_id))
        .where(Motion.user_id == current_user.id)
        .where(Motion.motion_type == "RFO")
    )
    motion = result.scalar_one_or_none()
    
    if not motion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="RFO motion not found"
        )
    
    # Get first step
    first_step = intake_service.get_step(1)
    if not first_step:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not load intake questions"
        )
    
    return IntakeStepResponse(
        step_number=first_step["step"],
        section=first_step["section"],
        title=first_step["title"],
        questions=first_step["questions"],
        progress=0.0,
        is_final_step=False
    )

@router.post("/rfo/step/{step_number}")
async def get_intake_step(
    step_number: int,
    request: IntakeStepRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific intake step with applicable questions"""
    # Verify motion ownership
    result = await db.execute(
        select(Motion)
        .where(Motion.id == uuid.UUID(request.motion_id))
        .where(Motion.user_id == current_user.id)
    )
    motion = result.scalar_one_or_none()
    
    if not motion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Motion not found"
        )
    
    # Get the requested step
    step = intake_service.get_step(step_number)
    if not step:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Step {step_number} not found"
        )
    
    # Check if step condition is met
    if "condition" in step:
        if not intake_service.evaluate_condition(step["condition"], request.answers):
            # Skip to next applicable step
            next_step = intake_service.get_next_step(step_number, request.answers)
            if next_step:
                step = next_step
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No applicable steps found based on your answers"
                )
    
    # Get applicable questions for this step
    applicable_questions = intake_service.get_applicable_questions(step, request.answers)
    
    # Calculate progress
    completed_steps = list(range(1, step_number))
    progress = intake_service.calculate_progress(completed_steps, request.answers)
    
    # Check if this is the final step
    next_step = intake_service.get_next_step(step_number, request.answers)
    is_final = next_step is None
    
    # Get required attachments if final step
    required_attachments = None
    if is_final and "relief_categories" in request.answers:
        required_attachments = intake_service.get_required_attachments(
            request.answers.get("relief_categories", [])
        )
    
    return IntakeStepResponse(
        step_number=step["step"],
        section=step["section"],
        title=step["title"],
        questions=applicable_questions,
        progress=progress,
        is_final_step=is_final,
        required_attachments=required_attachments
    )

@router.post("/rfo/submit-step")
async def submit_intake_step(
    submission: IntakeAnswerSubmit,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Submit answers for an intake step and get next step"""
    # Verify motion ownership
    result = await db.execute(
        select(Motion)
        .where(Motion.id == uuid.UUID(submission.motion_id))
        .where(Motion.user_id == current_user.id)
    )
    motion = result.scalar_one_or_none()
    
    if not motion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Motion not found"
        )
    
    # Get current step
    current_step = intake_service.get_step(submission.step_number)
    if not current_step:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Step {submission.step_number} not found"
        )
    
    # Validate answers
    errors = intake_service.validate_answers(current_step, submission.answers)
    if errors:
        return ValidationResponse(
            valid=False,
            errors=errors
        )
    
    # Save draft to database
    draft_result = await db.execute(
        select(MotionDraft)
        .where(MotionDraft.motion_id == motion.id)
        .where(MotionDraft.step_number == submission.step_number)
    )
    draft = draft_result.scalar_one_or_none()
    
    if draft:
        # Update existing draft
        draft.step_name = current_step["section"]
        draft.question_data = submission.answers
    else:
        # Create new draft
        draft = MotionDraft(
            motion_id=motion.id,
            step_number=submission.step_number,
            step_name=current_step["section"],
            question_data=submission.answers
        )
        db.add(draft)
    
    await db.commit()
    
    # Get all answers so far for condition evaluation
    all_drafts_result = await db.execute(
        select(MotionDraft)
        .where(MotionDraft.motion_id == motion.id)
        .order_by(MotionDraft.step_number)
    )
    all_drafts = all_drafts_result.scalars().all()
    
    # Combine all answers
    all_answers = {}
    for d in all_drafts:
        if d.question_data:
            all_answers.update(d.question_data)
    
    # Get next step
    next_step_data = intake_service.get_next_step(submission.step_number, all_answers)
    
    if next_step_data:
        # Check if next step condition is met
        while next_step_data and "condition" in next_step_data:
            if intake_service.evaluate_condition(next_step_data["condition"], all_answers):
                break
            next_step_data = intake_service.get_next_step(next_step_data["step"], all_answers)
        
        if next_step_data:
            applicable_questions = intake_service.get_applicable_questions(next_step_data, all_answers)
            completed_steps = [d.step_number for d in all_drafts]
            progress = intake_service.calculate_progress(completed_steps, all_answers)
            
            # Check if this is the final step
            final_check = intake_service.get_next_step(next_step_data["step"], all_answers)
            is_final = final_check is None
            
            # Get required attachments if final step
            required_attachments = None
            if is_final and "relief_categories" in all_answers:
                required_attachments = intake_service.get_required_attachments(
                    all_answers.get("relief_categories", [])
                )
            
            next_step_response = IntakeStepResponse(
                step_number=next_step_data["step"],
                section=next_step_data["section"],
                title=next_step_data["title"],
                questions=applicable_questions,
                progress=progress,
                is_final_step=is_final,
                required_attachments=required_attachments
            )
        else:
            next_step_response = None
    else:
        next_step_response = None
    
    return ValidationResponse(
        valid=True,
        errors={},
        next_step=next_step_response
    )

@router.get("/rfo/{motion_id}/summary")
async def get_intake_summary(
    motion_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get summary of all intake answers for a motion"""
    # Verify motion ownership
    result = await db.execute(
        select(Motion)
        .where(Motion.id == uuid.UUID(motion_id))
        .where(Motion.user_id == current_user.id)
    )
    motion = result.scalar_one_or_none()
    
    if not motion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Motion not found"
        )
    
    # Get all drafts
    drafts_result = await db.execute(
        select(MotionDraft)
        .where(MotionDraft.motion_id == motion.id)
        .order_by(MotionDraft.step_number)
    )
    drafts = drafts_result.scalars().all()
    
    # Combine all answers
    all_answers = {}
    step_summaries = []
    
    for draft in drafts:
        if draft.question_data:
            all_answers.update(draft.question_data)
            
            # Get step info
            step = intake_service.get_step(draft.step_number)
            if step:
                step_summaries.append({
                    "step_number": draft.step_number,
                    "section": step["section"],
                    "title": step["title"],
                    "answers": draft.question_data,
                    "has_llm_output": bool(draft.llm_output)
                })
    
    # Calculate overall progress
    all_steps = intake_service.get_all_steps()
    completed_steps = [d.step_number for d in drafts]
    progress = intake_service.calculate_progress(completed_steps, all_answers)
    
    # Get required attachments
    required_attachments = []
    if "relief_categories" in all_answers:
        required_attachments = intake_service.get_required_attachments(
            all_answers.get("relief_categories", [])
        )
    
    return {
        "motion_id": str(motion.id),
        "motion_type": motion.motion_type,
        "status": motion.status,
        "progress": progress,
        "total_steps_completed": len(drafts),
        "step_summaries": step_summaries,
        "all_answers": all_answers,
        "required_attachments": required_attachments,
        "ready_for_llm": progress >= 100
    }