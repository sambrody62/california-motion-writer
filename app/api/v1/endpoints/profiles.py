"""
Profile management endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional, List

from app.core.database import get_db
from app.models.user import User, Profile
from app.api.v1.endpoints.auth import get_current_user

router = APIRouter()


class ProfileCreate(BaseModel):
    case_number: Optional[str] = None
    county: Optional[str] = None
    court_branch: Optional[str] = None
    department: Optional[str] = None
    is_petitioner: Optional[bool] = True
    party_name: Optional[str] = None
    party_address: Optional[str] = None
    party_phone: Optional[str] = None
    other_party_name: Optional[str] = None
    other_party_address: Optional[str] = None
    other_party_attorney: Optional[str] = None
    children_info: Optional[List[dict]] = None


def _serialize_profile(profile: Profile) -> dict:
    return {
        "id": str(profile.id),
        "user_id": str(profile.user_id),
        "case_number": profile.case_number,
        "county": profile.county,
        "court_branch": profile.court_branch,
        "department": profile.department,
        "is_petitioner": profile.is_petitioner,
        "party_name": profile.party_name,
        "party_address": profile.party_address,
        "party_phone": profile.party_phone,
        "other_party_name": profile.other_party_name,
        "other_party_address": profile.other_party_address,
        "other_party_attorney": profile.other_party_attorney,
        "children_info": profile.children_info,
        "created_at": profile.created_at.isoformat() if profile.created_at else None,
        "updated_at": profile.updated_at.isoformat() if profile.updated_at else None,
    }


async def _get_profile_or_404(current_user: User, db: AsyncSession) -> Profile:
    result = await db.execute(
        select(Profile).where(Profile.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile


@router.post("/", status_code=201)
async def create_profile(
    profile_data: ProfileCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create user profile — returns 400 if one already exists (use PUT to update)"""
    result = await db.execute(
        select(Profile).where(Profile.user_id == current_user.id)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Profile already exists. Use PUT /profiles/me to update."
        )

    profile = Profile(
        user_id=current_user.id,
        **profile_data.model_dump()
    )
    db.add(profile)
    await db.commit()
    await db.refresh(profile)
    return _serialize_profile(profile)


@router.get("/")
async def get_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user profile"""
    profile = await _get_profile_or_404(current_user, db)
    return _serialize_profile(profile)


@router.get("/me")
async def get_my_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current user's profile"""
    profile = await _get_profile_or_404(current_user, db)
    return _serialize_profile(profile)


@router.put("/me")
async def update_my_profile(
    profile_data: ProfileCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update current user's profile"""
    profile = await _get_profile_or_404(current_user, db)

    for key, value in profile_data.model_dump(exclude_unset=True).items():
        setattr(profile, key, value)

    await db.commit()
    await db.refresh(profile)
    return _serialize_profile(profile)


@router.delete("/me", status_code=204)
async def delete_my_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete current user's profile"""
    profile = await _get_profile_or_404(current_user, db)
    await db.delete(profile)
    await db.commit()
