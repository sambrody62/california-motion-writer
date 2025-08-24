"""
Document generation endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
import logging
import uuid
import io
from datetime import datetime
from google.cloud import pubsub_v1
import json

from app.models.user import User
from app.models.motion import Motion, MotionDraft
from app.models.document import Document
from app.models.profile import Profile
from app.api.v1.endpoints.auth import get_current_user
from app.core.database import get_db
from app.core.config import settings
from app.services.pdf_service import pdf_service

router = APIRouter()
logger = logging.getLogger(__name__)

class GeneratePDFRequest(BaseModel):
    motion_id: str
    document_type: Optional[str] = None  # 'FL-300' or 'FL-320', auto-detect if not provided

class PDFGenerationResponse(BaseModel):
    document_id: str
    motion_id: str
    status: str
    download_url: Optional[str] = None

@router.post("/generate-pdf", response_model=PDFGenerationResponse)
async def generate_pdf(
    request: GeneratePDFRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Generate PDF document for motion"""
    try:
        # Verify motion ownership
        motion_result = await db.execute(
            select(Motion)
            .where(Motion.id == uuid.UUID(request.motion_id))
            .where(Motion.user_id == current_user.id)
        )
        motion = motion_result.scalar_one_or_none()
        
        if not motion:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Motion not found"
            )
        
        # Auto-detect document type if not provided
        document_type = request.document_type
        if not document_type:
            document_type = "FL-300" if motion.motion_type == "RFO" else "FL-320"
        
        # Create document record
        document = Document(
            motion_id=motion.id,
            document_type=document_type,
            filename=f"{motion.case_number or 'DRAFT'}_{document_type}_{datetime.now().strftime('%Y%m%d')}.pdf",
            generation_method="automated",
            gcs_url=""  # Will be updated after generation
        )
        db.add(document)
        await db.commit()
        await db.refresh(document)
        
        # Queue PDF generation as background task
        background_tasks.add_task(
            generate_pdf_background,
            str(document.id),
            str(motion.id),
            str(current_user.id),
            document_type
        )
        
        return PDFGenerationResponse(
            document_id=str(document.id),
            motion_id=request.motion_id,
            status="processing"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error initiating PDF generation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating PDF: {str(e)}"
        )

async def generate_pdf_background(
    document_id: str,
    motion_id: str,
    user_id: str,
    document_type: str
):
    """Background task to generate PDF"""
    try:
        # Publish to Pub/Sub for processing
        publisher = pubsub_v1.PublisherClient()
        topic_path = publisher.topic_path(settings.PROJECT_ID, settings.PUBSUB_TOPIC)
        
        message_data = {
            "action": "generate_pdf",
            "document_id": document_id,
            "motion_id": motion_id,
            "user_id": user_id,
            "document_type": document_type
        }
        
        future = publisher.publish(
            topic_path,
            json.dumps(message_data).encode('utf-8')
        )
        
        message_id = future.result()
        logger.info(f"Published PDF generation task to Pub/Sub: {message_id}")
        
    except Exception as e:
        logger.error(f"Error publishing to Pub/Sub: {str(e)}")

@router.post("/generate-pdf-sync")
async def generate_pdf_sync(
    request: GeneratePDFRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Generate PDF document synchronously (for testing/demo)"""
    try:
        # Get motion
        motion_result = await db.execute(
            select(Motion)
            .where(Motion.id == uuid.UUID(request.motion_id))
            .where(Motion.user_id == current_user.id)
        )
        motion = motion_result.scalar_one_or_none()
        
        if not motion:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Motion not found"
            )
        
        # Get user profile
        profile_result = await db.execute(
            select(Profile)
            .where(Profile.user_id == current_user.id)
        )
        profile = profile_result.scalar_one_or_none()
        
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User profile not found. Please complete your profile first."
            )
        
        # Get motion drafts with LLM output
        drafts_result = await db.execute(
            select(MotionDraft)
            .where(MotionDraft.motion_id == motion.id)
            .order_by(MotionDraft.step_number)
        )
        drafts = drafts_result.scalars().all()
        
        if not drafts:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No draft sections found for this motion"
            )
        
        # Prepare data for PDF generation
        profile_data = {
            "is_petitioner": profile.is_petitioner,
            "county": profile.county,
            "case_number": profile.case_number,
            "party_name": profile.party_name,
            "other_party_name": profile.other_party_name,
            "party_address": profile.party_address,
            "party_phone": profile.party_phone,
            "other_party_attorney": profile.other_party_attorney,
            "children_info": profile.children_info or []
        }
        
        motion_data = {
            "motion_type": motion.motion_type,
            "case_caption": motion.case_caption,
            "filing_date": motion.filing_date,
            "hearing_date": motion.hearing_date,
            "hearing_time": motion.hearing_time
        }
        
        llm_sections = [
            {
                "step_number": draft.step_number,
                "section": draft.step_name,
                "original_answers": draft.question_data,
                "rewritten_text": draft.llm_output or ""
            }
            for draft in drafts
        ]
        
        # Generate PDF
        pdf_bytes = await pdf_service.generate_motion_pdf(
            motion_type=motion.motion_type,
            motion_data=motion_data,
            profile_data=profile_data,
            llm_sections=llm_sections
        )
        
        # Create document record
        document = Document(
            motion_id=motion.id,
            document_type="FL-300" if motion.motion_type == "RFO" else "FL-320",
            filename=f"{profile.case_number or 'DRAFT'}_{motion.motion_type}_{datetime.now().strftime('%Y%m%d')}.pdf",
            file_size_bytes=len(pdf_bytes),
            generation_method="automated",
            gcs_url=""  # Would be uploaded to GCS in production
        )
        db.add(document)
        await db.commit()
        
        # Return PDF as stream
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={document.filename}"
            }
        )
        
    except HTTPException:
        raise
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Form template not found. Please ensure official forms are in the forms/ directory: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error generating PDF: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating PDF: {str(e)}"
        )

@router.get("/{document_id}/download")
async def download_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Download generated document"""
    try:
        # Get document and verify ownership
        result = await db.execute(
            select(Document, Motion)
            .join(Motion, Document.motion_id == Motion.id)
            .where(Document.id == uuid.UUID(document_id))
            .where(Motion.user_id == current_user.id)
        )
        row = result.first()
        
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        document, motion = row
        
        # For now, return error if GCS URL not available
        # In production, this would download from GCS
        if not document.gcs_url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Document not yet available. Please try again later."
            )
        
        # TODO: Download from GCS and return
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="GCS download not yet implemented"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading document: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error downloading document: {str(e)}"
        )

@router.get("/motion/{motion_id}/documents")
async def list_motion_documents(
    motion_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all documents for a motion"""
    try:
        # Verify motion ownership
        motion_result = await db.execute(
            select(Motion)
            .where(Motion.id == uuid.UUID(motion_id))
            .where(Motion.user_id == current_user.id)
        )
        motion = motion_result.scalar_one_or_none()
        
        if not motion:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Motion not found"
            )
        
        # Get documents
        docs_result = await db.execute(
            select(Document)
            .where(Document.motion_id == motion.id)
            .order_by(Document.generated_at.desc())
        )
        documents = docs_result.scalars().all()
        
        return {
            "motion_id": str(motion.id),
            "documents": [
                {
                    "id": str(doc.id),
                    "document_type": doc.document_type,
                    "filename": doc.filename,
                    "file_size_bytes": doc.file_size_bytes,
                    "generated_at": doc.generated_at,
                    "available": bool(doc.gcs_url)
                }
                for doc in documents
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing documents: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing documents: {str(e)}"
        )