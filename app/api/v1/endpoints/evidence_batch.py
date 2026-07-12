"""
Bulk text-screenshot import: OCR + threading analysis for the evidence flow.

Analysis only — this endpoint persists nothing (mirrors the transient
suggested_transcription pattern). The frontend review screen saves the final
transcript through the normal POST /motions/{id}/evidence with user_confirmed.
"""
import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.endpoints.auth import get_current_user
from app.api.v1.endpoints.evidence import _get_owned_motion
from app.core.database import get_db
from app.models.user import User
from app.services import ocr_service, text_thread_service

router = APIRouter()
logger = logging.getLogger(__name__)

MAX_FILES = 20
MAX_FILE_BYTES = 10 * 1024 * 1024  # 10 MB each
IMAGE_EXTENSIONS = frozenset(["png", "jpg", "jpeg"])
# Anthropic vision limits (~5MB/image, ~32MB/request incl. base64 inflation)
MAX_VISION_IMAGE_BYTES = int(4.5 * 1024 * 1024)
MAX_VISION_TOTAL_BYTES = 20 * 1024 * 1024
_MEDIA_TYPES = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg"}


class PerFileResult(BaseModel):
    filename: str
    ok: bool
    chars: int


class BatchUploadResponse(BaseModel):
    merged_transcript: str
    participants: List[str]
    date_range: dict
    suggested_source_date: Optional[str] = None
    per_file: List[PerFileResult]
    notice: Optional[str] = None


def _validate_files(files: List[UploadFile]) -> None:
    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="No files provided."
        )
    if len(files) > MAX_FILES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Too many files. Maximum is {MAX_FILES} screenshots per import.",
        )
    for file in files:
        ext = (file.filename or "").rsplit(".", 1)[-1].lower()
        if ext not in IMAGE_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"'{file.filename}': only PNG and JPG screenshots are supported.",
            )


@router.post("/motions/{motion_id}/evidence/batch-upload", response_model=BatchUploadResponse)
async def batch_upload(
    motion_id: str,
    files: List[UploadFile] = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Read the screenshots (Claude vision → OCR fallback) into one transcript."""
    await _get_owned_motion(motion_id, current_user, db)
    _validate_files(files)

    loaded = []  # [{"filename", "content", "media_type"}]
    for file in files:
        content = await file.read()
        if len(content) > MAX_FILE_BYTES:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"'{file.filename}' is too large. Maximum size is 10 MB.",
            )
        ext = (file.filename or "").rsplit(".", 1)[-1].lower()
        loaded.append({
            "filename": file.filename or "",
            "content": content,
            "media_type": _MEDIA_TYPES.get(ext, "image/png"),
        })

    # 1. Claude vision — reads bubbles directly (sender sides, timestamps)
    vision_images = [i for i in loaded if len(i["content"]) <= MAX_VISION_IMAGE_BYTES]
    if sum(len(i["content"]) for i in vision_images) <= MAX_VISION_TOTAL_BYTES:
        vision_result = await text_thread_service.read_screenshot_images(
            vision_images, user_id=str(current_user.id)
        )
        if vision_result is not None:
            included = {i["filename"] for i in vision_images}
            per_file = [
                PerFileResult(filename=i["filename"], ok=i["filename"] in included, chars=0)
                for i in loaded
            ]
            logger.info(
                "Batch upload via vision: motion=%s files=%d sent=%d",
                motion_id, len(loaded), len(vision_images),
            )
            return BatchUploadResponse(per_file=per_file, **{
                k: vision_result[k]
                for k in ("merged_transcript", "participants", "date_range",
                          "suggested_source_date", "notice")
            })

    # 2. OCR + threading fallback
    ocr_texts = []
    per_file: List[PerFileResult] = []
    ocr_on = ocr_service.ocr_enabled()
    for item in loaded:
        text = ocr_service.extract_text(item["content"]) if ocr_on else ""
        ok = bool(text.strip())
        per_file.append(PerFileResult(filename=item["filename"], ok=ok, chars=len(text)))
        if ok:
            ocr_texts.append({"filename": item["filename"], "text": text})

    logger.info(
        "Batch upload analysis: motion=%s files=%d readable=%d",
        motion_id, len(files), len(ocr_texts),
    )

    if not ocr_texts:
        return BatchUploadResponse(
            merged_transcript="",
            participants=[],
            date_range={"start": None, "end": None},
            suggested_source_date=None,
            per_file=per_file,
            notice=text_thread_service.NOTICE_NO_TEXT,
        )

    result = await text_thread_service.thread_screenshots(
        ocr_texts, user_id=str(current_user.id)
    )
    return BatchUploadResponse(
        merged_transcript=result["merged_transcript"],
        participants=result["participants"],
        date_range=result["date_range"],
        suggested_source_date=result["suggested_source_date"],
        per_file=per_file,
        notice=result["notice"],
    )
