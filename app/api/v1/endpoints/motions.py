"""
Motion management endpoints
"""
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
import uuid
import json

from app.core.database import get_db
from app.models.user import User
from app.models.motion import Motion, MotionDraft
from app.api.v1.endpoints.auth import get_current_user

router = APIRouter()

class MotionCreate(BaseModel):
    motion_type: str  # 'RFO' or 'RESPONSE'
    case_caption: Optional[str] = None

class MotionResponse(BaseModel):
    id: str
    motion_type: str
    status: str
    created_at: datetime
    updated_at: datetime

class DraftUpdate(BaseModel):
    step_number: int
    step_name: str
    question_data: dict

@router.post("/", response_model=MotionResponse)
async def create_motion(
    motion_data: MotionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new motion"""
    # Validate motion type
    if motion_data.motion_type not in ["RFO", "RESPONSE"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid motion type. Must be 'RFO' or 'RESPONSE'"
        )
    
    # Create motion
    motion = Motion(
        user_id=current_user.id,
        motion_type=motion_data.motion_type,
        case_caption=motion_data.case_caption,
        status="draft"
    )
    
    db.add(motion)
    await db.commit()
    await db.refresh(motion)
    
    return MotionResponse(
        id=str(motion.id),
        motion_type=motion.motion_type,
        status=motion.status,
        created_at=motion.created_at,
        updated_at=motion.updated_at
    )

@router.get("/", response_model=List[MotionResponse])
async def list_motions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all motions for current user"""
    result = await db.execute(
        select(Motion)
        .where(Motion.user_id == current_user.id)
        .order_by(Motion.created_at.desc())
    )
    motions = result.scalars().all()
    
    return [
        MotionResponse(
            id=str(motion.id),
            motion_type=motion.motion_type,
            status=motion.status,
            created_at=motion.created_at,
            updated_at=motion.updated_at
        )
        for motion in motions
    ]

@router.get("/{motion_id}")
async def get_motion(
    motion_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get motion details with all drafts"""
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
    
    # Get drafts
    drafts_result = await db.execute(
        select(MotionDraft)
        .where(MotionDraft.motion_id == motion.id)
        .order_by(MotionDraft.step_number)
    )
    drafts = drafts_result.scalars().all()
    
    return {
        "id": str(motion.id),
        "motion_type": motion.motion_type,
        "status": motion.status,
        "case_caption": motion.case_caption,
        "created_at": motion.created_at,
        "drafts": [
            {
                "step_number": draft.step_number,
                "step_name": draft.step_name,
                "question_data": draft.question_data,
                "llm_output": draft.llm_output,
                "is_complete": draft.is_complete
            }
            for draft in drafts
        ]
    }

@router.post("/{motion_id}/drafts")
async def save_draft(
    motion_id: str,
    draft_data: DraftUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Save or update a draft step"""
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
    
    # Check if draft exists
    draft_result = await db.execute(
        select(MotionDraft)
        .where(MotionDraft.motion_id == motion.id)
        .where(MotionDraft.step_number == draft_data.step_number)
    )
    draft = draft_result.scalar_one_or_none()
    
    if draft:
        # Update existing draft
        draft.step_name = draft_data.step_name
        draft.question_data = draft_data.question_data
        draft.updated_at = datetime.utcnow()
    else:
        # Create new draft
        draft = MotionDraft(
            motion_id=motion.id,
            step_number=draft_data.step_number,
            step_name=draft_data.step_name,
            question_data=draft_data.question_data
        )
        db.add(draft)
    
    await db.commit()
    
    return {"message": "Draft saved successfully", "step": draft_data.step_number}

@router.post("/{motion_id}/complete")
async def complete_motion(
    motion_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Mark motion as completed"""
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
    
    motion.status = "completed"
    motion.completed_at = datetime.utcnow()
    await db.commit()
    
    return {"message": "Motion marked as completed", "id": str(motion.id)}