"""
Evidence management endpoints.
"""
import json
import logging
from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.evidence import Evidence
from app.models.motion import Motion
from app.models.user import User
from app.api.v1.endpoints.auth import get_current_user
from app.services import evidence_storage_service
from app.services import ocr_service

logger = logging.getLogger(__name__)

router = APIRouter()

VALID_TAGS = frozenset(["threat", "non_payment", "custody_violation", "promise_to_follow", "false_claim", "other"])
ALLOWED_EXTENSIONS = frozenset(["png", "jpg", "jpeg", "pdf", "txt"])
IMAGE_EXTENSIONS = frozenset(["png", "jpg", "jpeg"])
MAX_FILE_BYTES = 10 * 1024 * 1024  # 10 MB


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class EvidenceCreate(BaseModel):
    evidence_type: str
    tags: List[str]
    source_date: Optional[date] = None
    description: str
    transcription: Optional[str] = None
    # The bulk-import review screen confirms in the same step as creation
    user_confirmed: bool = False


class EvidenceUpdate(BaseModel):
    tags: Optional[List[str]] = None
    transcription: Optional[str] = None
    user_confirmed: Optional[bool] = None


class EvidenceResponse(BaseModel):
    id: str
    motion_id: str
    user_id: str
    evidence_type: str
    tags: List[str]
    source_date: Optional[date]
    description: str
    transcription: Optional[str]
    filename: Optional[str]
    storage_path: Optional[str]
    user_confirmed: bool
    created_at: str
    # OCR suggestion — transient, never persisted. None when OCR is off or file is not an image.
    suggested_transcription: Optional[str] = None

    @classmethod
    def from_orm(cls, ev: Evidence) -> "EvidenceResponse":
        return cls(
            id=str(ev.id),
            motion_id=str(ev.motion_id),
            user_id=str(ev.user_id),
            evidence_type=ev.evidence_type,
            tags=ev.tags or [],
            source_date=ev.source_date,
            description=ev.description,
            transcription=ev.transcription,
            filename=ev.filename,
            storage_path=ev.storage_path,
            user_confirmed=ev.user_confirmed,
            created_at=ev.created_at.isoformat() if ev.created_at else "",
        )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _validate_tags(tags: List[str]) -> None:
    invalid = [t for t in tags if t not in VALID_TAGS]
    if invalid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid tag(s): {invalid}. Allowed: {sorted(VALID_TAGS)}",
        )


async def _get_owned_motion(motion_id: str, user: User, db: AsyncSession) -> Motion:
    result = await db.execute(
        select(Motion)
        .where(Motion.id == motion_id)
        .where(Motion.user_id == str(user.id))
    )
    motion = result.scalar_one_or_none()
    if not motion:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Motion not found")
    return motion


async def _get_owned_evidence(evidence_id: str, user: User, db: AsyncSession) -> Evidence:
    result = await db.execute(
        select(Evidence)
        .where(Evidence.id == evidence_id)
        .where(Evidence.user_id == str(user.id))
    )
    ev = result.scalar_one_or_none()
    if not ev:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence not found")
    return ev


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/motions/{motion_id}/evidence", response_model=EvidenceResponse, status_code=201)
async def create_evidence(
    motion_id: str,
    payload: EvidenceCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Attach a text/metadata evidence record to a motion."""
    await _get_owned_motion(motion_id, current_user, db)
    _validate_tags(payload.tags)

    ev = Evidence(
        motion_id=motion_id,
        user_id=str(current_user.id),
        evidence_type=payload.evidence_type,
        tags=payload.tags,
        source_date=payload.source_date,
        description=payload.description,
        transcription=payload.transcription,
        user_confirmed=payload.user_confirmed,
    )
    db.add(ev)
    await db.commit()
    await db.refresh(ev)
    logger.info("Evidence created id=%s", ev.id)
    return EvidenceResponse.from_orm(ev)


@router.post("/motions/{motion_id}/evidence/upload", response_model=EvidenceResponse, status_code=201)
async def upload_evidence(
    motion_id: str,
    file: UploadFile = File(...),
    evidence_type: str = Form(...),
    tags: str = Form(...),  # JSON-encoded list e.g. '["threat"]'
    description: str = Form(...),
    source_date: Optional[str] = Form(None),
    transcription: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload a file as evidence attached to a motion."""
    await _get_owned_motion(motion_id, current_user, db)

    # Parse and validate tags
    try:
        tag_list: List[str] = json.loads(tags)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="tags must be a JSON-encoded list")
    _validate_tags(tag_list)

    # Validate filename
    raw_name = file.filename or ""
    clean_name = evidence_storage_service._sanitize_filename(raw_name)
    if not clean_name:
        raise HTTPException(status_code=400, detail="Filename must not be empty")

    ext = clean_name.rsplit(".", 1)[-1].lower() if "." in clean_name else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type '.{ext}' not allowed. Allowed: {sorted(ALLOWED_EXTENSIONS)}",
        )

    content = await file.read()
    if len(content) > MAX_FILE_BYTES:
        raise HTTPException(status_code=413, detail="File exceeds 10 MB limit")

    parsed_date: Optional[date] = None
    if source_date:
        try:
            parsed_date = date.fromisoformat(source_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="source_date must be YYYY-MM-DD")

    try:
        storage_path = evidence_storage_service.save_file(motion_id, clean_name, content)
    except evidence_storage_service.EvidenceStorageError:
        raise HTTPException(
            status_code=502,
            detail="We couldn't store your file — nothing was saved. Please try again.",
        )

    ev = Evidence(
        motion_id=motion_id,
        user_id=str(current_user.id),
        evidence_type=evidence_type,
        tags=tag_list,
        source_date=parsed_date,
        description=description,
        transcription=transcription,  # never auto-set from OCR
        filename=clean_name,
        storage_path=storage_path,
    )
    db.add(ev)
    await db.commit()
    await db.refresh(ev)
    logger.info("Evidence file uploaded id=%s", ev.id)

    response = EvidenceResponse.from_orm(ev)

    # OCR suggestion — only for images when feature flag is on.
    # Suggestion is transient: never persisted, user must edit and confirm.
    if ocr_service.ocr_enabled() and ext in IMAGE_EXTENSIONS:
        suggested = ocr_service.extract_text(content)
        if suggested:
            response.suggested_transcription = suggested
            logger.info("OCR suggestion generated for evidence id=%s", ev.id)

    return response


@router.get("/motions/{motion_id}/evidence", response_model=List[EvidenceResponse])
async def list_evidence(
    motion_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all evidence for a motion."""
    await _get_owned_motion(motion_id, current_user, db)

    result = await db.execute(
        select(Evidence)
        .where(Evidence.motion_id == motion_id)
        .order_by(Evidence.created_at)
    )
    items = result.scalars().all()
    return [EvidenceResponse.from_orm(e) for e in items]


@router.put("/evidence/{evidence_id}", response_model=EvidenceResponse)
async def update_evidence(
    evidence_id: str,
    payload: EvidenceUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update tags, transcription, or user_confirmed on an evidence record."""
    ev = await _get_owned_evidence(evidence_id, current_user, db)

    if payload.tags is not None:
        _validate_tags(payload.tags)
        ev.tags = payload.tags
    if payload.transcription is not None:
        ev.transcription = payload.transcription
    if payload.user_confirmed is not None:
        ev.user_confirmed = payload.user_confirmed

    await db.commit()
    await db.refresh(ev)
    logger.info("Evidence updated id=%s", ev.id)
    return EvidenceResponse.from_orm(ev)


@router.delete("/evidence/{evidence_id}", status_code=204)
async def delete_evidence(
    evidence_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete an evidence record."""
    ev = await _get_owned_evidence(evidence_id, current_user, db)
    await db.delete(ev)
    await db.commit()
    logger.info("Evidence deleted id=%s", evidence_id)
