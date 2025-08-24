"""
Profile management endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional, List

from app.core.database import get_db
from app.models.user import User, Profile
from app.api.v1.endpoints.auth import get_current_user

router = APIRouter()

class ProfileCreate(BaseModel):
    case_number: Optional[str]
    county: str
    court_branch: Optional[str]
    department: Optional[str]
    is_petitioner: bool
    party_name: str
    party_address: Optional[str]
    party_phone: Optional[str]
    other_party_name: str
    other_party_address: Optional[str]
    other_party_attorney: Optional[str]
    children_info: Optional[List[dict]]

@router.post("/")
async def create_or_update_profile(
    profile_data: ProfileCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create or update user profile"""
    # Check if profile exists
    result = await db.execute(
        select(Profile).where(Profile.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()
    
    if profile:
        # Update existing
        for key, value in profile_data.dict().items():
            setattr(profile, key, value)
    else:
        # Create new
        profile = Profile(
            user_id=current_user.id,
            **profile_data.dict()
        )
        db.add(profile)
    
    await db.commit()
    return {"message": "Profile saved successfully"}

@router.get("/")
async def get_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user profile"""
    result = await db.execute(
        select(Profile).where(Profile.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()
    
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    return profile