"""
Core dependencies for the application
"""
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from jose import JWTError, jwt

from app.core.config import settings
from app.core.database import get_db
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get the current authenticated user from JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if user is None:
        raise credentials_exception
    return user

async def get_current_user_ws(
    token: str,
    db: AsyncSession
) -> Optional[User]:
    """
    Get the current authenticated user from JWT token for WebSocket
    Returns None instead of raising exceptions for WebSocket compatibility
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            return None
    except JWTError:
        return None

    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    return user

async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Ensure the user is active"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

async def get_verified_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Ensure the user's email is verified"""
    if not current_user.email_verified:
        raise HTTPException(
            status_code=403,
            detail="Please verify your email address"
        )
    return current_user

__all__ = [
    'get_db',
    'get_current_user',
    'get_current_user_ws',
    'get_current_active_user',
    'get_verified_user',
    'oauth2_scheme'
]