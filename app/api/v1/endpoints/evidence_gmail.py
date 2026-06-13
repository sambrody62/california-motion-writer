"""
Gmail evidence import endpoints — ALL guarded by GMAIL_EVIDENCE_ENABLED flag.

When the flag is off every endpoint returns 404 so the feature is completely inert.
Access tokens are accepted in request bodies and used within the request only —
they are never written to any database column.
"""
import os
import logging
from typing import List, Optional
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.evidence import Evidence
from app.models.motion import Motion
from app.models.user import User
from app.api.v1.endpoints.auth import get_current_user
from app.api.v1.endpoints.evidence import EvidenceResponse
from app.services import gmail_evidence_service

logger = logging.getLogger(__name__)

router = APIRouter()


def _require_flag() -> None:
    """Raise 404 when the Gmail feature flag is off."""
    if os.getenv("GMAIL_EVIDENCE_ENABLED", "false") != "true":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")


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


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class ExchangeRequest(BaseModel):
    code: str


class ScanRequest(BaseModel):
    access_token: str


class ImportRequest(BaseModel):
    access_token: str
    message_ids: List[str]


class AuthUrlResponse(BaseModel):
    auth_url: str


class ExchangeResponse(BaseModel):
    access_token: str


class CandidateResponse(BaseModel):
    message_id: str
    from_: str
    date: str
    subject: str
    snippet: str

    class Config:
        populate_by_name = True

    @classmethod
    def from_dict(cls, d: dict) -> "CandidateResponse":
        return cls(
            message_id=d["message_id"],
            from_=d.get("from", ""),
            date=d.get("date", ""),
            subject=d.get("subject", ""),
            snippet=d.get("snippet", ""),
        )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/evidence/gmail/auth-url", response_model=AuthUrlResponse)
async def get_auth_url(current_user: User = Depends(get_current_user)):
    """Return the Google OAuth consent URL for gmail.readonly."""
    _require_flag()
    url = gmail_evidence_service.get_auth_url()
    return AuthUrlResponse(auth_url=url)


@router.post("/evidence/gmail/exchange", response_model=ExchangeResponse)
async def exchange_code(
    payload: ExchangeRequest,
    current_user: User = Depends(get_current_user),
):
    """Exchange an OAuth authorization code for a short-lived access token.

    The token is returned to the client only — it is NOT stored server-side.
    """
    _require_flag()
    token = gmail_evidence_service.exchange_code(payload.code)
    return ExchangeResponse(access_token=token)


@router.post("/motions/{motion_id}/evidence/gmail/scan")
async def scan_gmail(
    motion_id: str,
    payload: ScanRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return candidate Gmail messages (metadata + snippet only, no full bodies)."""
    _require_flag()
    motion = await _get_owned_motion(motion_id, current_user, db)

    # Derive other-party info from the motion's profile if available
    other_name: Optional[str] = None
    other_email: Optional[str] = None
    if motion.profile_id:
        from app.models.user import Profile
        profile_result = await db.execute(
            select(Profile).where(Profile.id == str(motion.profile_id))
        )
        profile = profile_result.scalar_one_or_none()
        if profile:
            other_name = profile.other_party_name

    candidates = gmail_evidence_service.scan_emails(
        payload.access_token, other_name, other_email
    )
    logger.info(
        "Gmail scan returned %d candidates for motion_id=%s", len(candidates), motion_id
    )
    # Return dicts directly — no full bodies in the response
    return [
        {
            "message_id": c["message_id"],
            "from": c.get("from", ""),
            "date": c.get("date", ""),
            "subject": c.get("subject", ""),
            "snippet": c.get("snippet", ""),
        }
        for c in candidates
    ]


@router.post(
    "/motions/{motion_id}/evidence/gmail/import",
    response_model=List[EvidenceResponse],
    status_code=201,
)
async def import_gmail_evidence(
    motion_id: str,
    payload: ImportRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Fetch selected email bodies and save them as unconfirmed Evidence rows.

    - evidence_type = 'email'
    - user_confirmed = False  (human confirmation is always required)
    - transcription = body_text  (editable suggestion)
    - tags = []  (user assigns tags after review)
    - access_token is used within this request and never written to any column
    """
    _require_flag()
    await _get_owned_motion(motion_id, current_user, db)

    bodies = gmail_evidence_service.fetch_bodies(payload.access_token, payload.message_ids)

    created = []
    for msg_id, body in bodies.items():
        parsed_date: Optional[date] = None
        if body.get("date"):
            try:
                parsed_date = date.fromisoformat(body["date"])
            except ValueError:
                parsed_date = None

        ev = Evidence(
            motion_id=motion_id,
            user_id=str(current_user.id),
            evidence_type="email",
            tags=[],
            source_date=parsed_date,
            description=body.get("subject", ""),
            transcription=body.get("body_text", ""),
            filename=None,
            storage_path=None,
            user_confirmed=False,
        )
        db.add(ev)
        await db.flush()
        logger.info("Gmail evidence created id=%s message_id=%s", ev.id, msg_id)
        created.append(ev)

    await db.commit()
    for ev in created:
        await db.refresh(ev)

    return [EvidenceResponse.from_orm(ev) for ev in created]
