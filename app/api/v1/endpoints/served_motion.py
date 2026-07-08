"""
Parse an uploaded served motion (FL-300) to pre-fill the FL-320 response wizard.

The file is read once, parsed, and discarded — never written to disk or DB.
"""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel

from app.api.v1.endpoints.auth import get_current_user
from app.models.user import User
from app.services import served_motion_parser

router = APIRouter()
logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = frozenset(["pdf", "png", "jpg", "jpeg"])
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


class ServedMotionParseResponse(BaseModel):
    success: bool
    # Plain dict, not a typed model: only whitelisted keys are ever present
    # (see served_motion_parser.sanitize_extracted) and absent means "not found"
    extracted: dict
    notice: Optional[str] = None


@router.post("/parse-served-motion", response_model=ServedMotionParseResponse)
async def parse_served_motion(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    """Extract structured facts from the motion the user was served."""
    ext = (file.filename or "").rsplit(".", 1)[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type '.{ext}' not allowed. Allowed: {sorted(ALLOWED_EXTENSIONS)}",
        )

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File too large. Maximum size is 10 MB.",
        )

    logger.info("Parsing served motion: ext=%s size=%d", ext, len(content))
    result = await served_motion_parser.parse_served_motion(content, ext)

    return ServedMotionParseResponse(
        success=True,
        extracted=result["extracted"],
        notice=result["notice"],
    )
