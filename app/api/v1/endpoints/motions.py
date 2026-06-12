"""
Motion management endpoints
"""
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.core.database import get_db
from app.models.user import User
from app.models.motion import Motion, MotionDraft, MotionType
from app.api.v1.endpoints.auth import get_current_user

router = APIRouter()


class MotionCreate(BaseModel):
    motion_type: str
    case_caption: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    filing_track: Optional[str] = None
    courthouse: Optional[str] = None
    intake_data: Optional[dict] = None


class MotionUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None


class MotionResponse(BaseModel):
    id: str
    motion_type: str
    status: str
    title: Optional[str] = None
    description: Optional[str] = None
    filing_track: Optional[str] = None
    courthouse: Optional[str] = None
    intake_data: Optional[dict] = None
    created_at: datetime
    updated_at: datetime


class DraftUpdate(BaseModel):
    step_number: int
    step_name: str
    question_data: dict


def _motion_to_response(motion: Motion) -> MotionResponse:
    return MotionResponse(
        id=str(motion.id),
        motion_type=motion.motion_type.value if hasattr(motion.motion_type, "value") else motion.motion_type,
        status=motion.status,
        title=motion.title,
        description=motion.description,
        filing_track=motion.filing_track,
        courthouse=motion.courthouse,
        intake_data=motion.intake_data,
        created_at=motion.created_at,
        updated_at=motion.updated_at,
    )


def _validate_motion_type(motion_type: str) -> MotionType:
    valid_types = [e.value for e in MotionType]
    if motion_type not in valid_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid motion type. Must be one of: {', '.join(valid_types)}"
        )
    return next(e for e in MotionType if e.value == motion_type)


@router.post("/", response_model=MotionResponse, status_code=201)
async def create_motion(
    motion_data: MotionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new motion"""
    motion_type_enum = _validate_motion_type(motion_data.motion_type)

    motion = Motion(
        user_id=str(current_user.id),
        motion_type=motion_type_enum,
        case_caption=motion_data.case_caption,
        title=motion_data.title,
        description=motion_data.description,
        filing_track=motion_data.filing_track,
        courthouse=motion_data.courthouse,
        intake_data=motion_data.intake_data,
        status="draft",
    )
    db.add(motion)
    await db.commit()
    await db.refresh(motion)
    return _motion_to_response(motion)


@router.get("/", response_model=List[MotionResponse])
async def list_motions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all motions for current user"""
    result = await db.execute(
        select(Motion)
        .where(Motion.user_id == str(current_user.id))
        .order_by(Motion.created_at.desc())
    )
    motions = result.scalars().all()
    return [_motion_to_response(m) for m in motions]


@router.get("/{motion_id}")
async def get_motion(
    motion_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get motion details with all drafts"""
    result = await db.execute(
        select(Motion)
        .where(Motion.id == motion_id)
        .where(Motion.user_id == str(current_user.id))
    )
    motion = result.scalar_one_or_none()

    if not motion:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Motion not found")

    drafts_result = await db.execute(
        select(MotionDraft)
        .where(MotionDraft.motion_id == motion.id)
        .order_by(MotionDraft.step_number)
    )
    drafts = drafts_result.scalars().all()

    motion_type_val = motion.motion_type.value if hasattr(motion.motion_type, "value") else motion.motion_type
    return {
        "id": str(motion.id),
        "motion_type": motion_type_val,
        "status": motion.status,
        "title": motion.title,
        "description": motion.description,
        "case_caption": motion.case_caption,
        "filing_track": motion.filing_track,
        "courthouse": motion.courthouse,
        "intake_data": motion.intake_data,
        "created_at": motion.created_at,
        "updated_at": motion.updated_at,
        "drafts": [
            {
                "step_number": d.step_number,
                "step_name": d.step_name,
                "question_data": d.question_data,
                "llm_output": d.llm_output,
                "is_complete": d.is_complete,
            }
            for d in drafts
        ],
    }


@router.put("/{motion_id}", response_model=MotionResponse)
async def update_motion(
    motion_id: str,
    update_data: MotionUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update motion title, description, or status"""
    result = await db.execute(
        select(Motion)
        .where(Motion.id == motion_id)
        .where(Motion.user_id == str(current_user.id))
    )
    motion = result.scalar_one_or_none()

    if not motion:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Motion not found")

    for field, value in update_data.model_dump(exclude_unset=True).items():
        setattr(motion, field, value)
    motion.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(motion)
    return _motion_to_response(motion)


@router.delete("/{motion_id}", status_code=204)
async def delete_motion(
    motion_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a motion"""
    result = await db.execute(
        select(Motion)
        .where(Motion.id == motion_id)
        .where(Motion.user_id == str(current_user.id))
    )
    motion = result.scalar_one_or_none()

    if not motion:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Motion not found")

    await db.delete(motion)
    await db.commit()


@router.post("/{motion_id}/drafts")
async def save_draft(
    motion_id: str,
    draft_data: DraftUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Save or update a draft step"""
    result = await db.execute(
        select(Motion)
        .where(Motion.id == motion_id)
        .where(Motion.user_id == str(current_user.id))
    )
    motion = result.scalar_one_or_none()

    if not motion:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Motion not found")

    draft_result = await db.execute(
        select(MotionDraft)
        .where(MotionDraft.motion_id == motion.id)
        .where(MotionDraft.step_number == draft_data.step_number)
    )
    draft = draft_result.scalar_one_or_none()

    if draft:
        draft.step_name = draft_data.step_name
        draft.question_data = draft_data.question_data
        draft.updated_at = datetime.utcnow()
    else:
        draft = MotionDraft(
            motion_id=motion.id,
            step_number=draft_data.step_number,
            step_name=draft_data.step_name,
            question_data=draft_data.question_data,
        )
        db.add(draft)

    await db.commit()
    await db.refresh(draft)

    return {
        "message": "Draft saved successfully",
        "step_number": draft.step_number,
        "question_data": draft.question_data,
    }


@router.post("/{motion_id}/complete")
async def complete_motion(
    motion_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Mark motion as completed"""
    result = await db.execute(
        select(Motion)
        .where(Motion.id == motion_id)
        .where(Motion.user_id == str(current_user.id))
    )
    motion = result.scalar_one_or_none()

    if not motion:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Motion not found")

    motion.status = "completed"
    motion.completed_at = datetime.utcnow()
    await db.commit()

    return {"message": "Motion marked as completed", "id": str(motion.id)}
