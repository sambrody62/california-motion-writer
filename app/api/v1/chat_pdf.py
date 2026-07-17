"""
API endpoints for chat-to-PDF workflow
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.core.deps import get_db, get_current_user
from app.core.entitlements import require_active_subscription
from app.models.user import User
from app.services.chat_to_pdf_service import chat_to_pdf_service

router = APIRouter(prefix="/chat-pdf", tags=["chat-pdf"])

class PrepareMotionRequest(BaseModel):
    session_id: str

class GeneratePDFRequest(BaseModel):
    motion_id: str

class GetMissingInfoRequest(BaseModel):
    session_id: str

@router.post("/prepare-motion")
async def prepare_motion_from_chat(
    request: PrepareMotionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Prepare motion data from chat conversation

    This endpoint:
    1. Extracts data from chat conversation
    2. Maps to form fields
    3. Creates motion record
    4. Validates completeness
    """
    try:
        result = await chat_to_pdf_service.prepare_motion_from_chat(
            db,
            request.session_id,
            str(current_user.id)
        )

        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Failed to prepare motion")
            )

        return result

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error preparing motion: {str(e)}"
        )

@router.post("/generate-pdf", dependencies=[Depends(require_active_subscription)])
async def generate_pdf_from_motion(
    request: GeneratePDFRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate PDF documents from prepared motion

    This endpoint:
    1. Retrieves motion data
    2. Generates individual form PDFs
    3. Creates combined packet
    4. Updates motion status
    """
    try:
        result = await chat_to_pdf_service.generate_pdf_from_motion(
            db,
            request.motion_id,
            str(current_user.id)
        )

        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Failed to generate PDF")
            )

        return result

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating PDF: {str(e)}"
        )

@router.post("/missing-info")
async def get_missing_information(
    request: GetMissingInfoRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get list of missing information needed for forms

    Returns questions for any missing required fields
    """
    try:
        missing_info = await chat_to_pdf_service.get_missing_information(
            db,
            request.session_id
        )

        return {
            "success": True,
            "missing_fields": missing_info,
            "count": len(missing_info)
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error checking missing information: {str(e)}"
        )

@router.get("/summary/{session_id}")
async def get_confirmation_summary(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a confirmation summary of collected information

    Returns formatted summary for user review
    """
    try:
        summary = await chat_to_pdf_service.create_confirmation_summary(
            db,
            session_id
        )

        return {
            "success": True,
            "summary": summary
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating summary: {str(e)}"
        )

@router.post("/complete-workflow", dependencies=[Depends(require_active_subscription)])
async def complete_chat_to_pdf_workflow(
    request: PrepareMotionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Complete the entire chat-to-PDF workflow in one call

    This endpoint:
    1. Prepares motion from chat
    2. Generates PDFs if data is complete
    3. Returns results or missing information
    """
    try:
        # First prepare the motion
        prepare_result = await chat_to_pdf_service.prepare_motion_from_chat(
            db,
            request.session_id,
            str(current_user.id)
        )

        if not prepare_result["success"]:
            return prepare_result

        # Check if ready for PDF generation
        if prepare_result.get("ready_for_pdf", False):
            # Generate PDFs
            pdf_result = await chat_to_pdf_service.generate_pdf_from_motion(
                db,
                prepare_result["motion_id"],
                str(current_user.id)
            )

            return {
                "success": True,
                "workflow_complete": True,
                "motion_id": prepare_result["motion_id"],
                "pdfs_generated": pdf_result.get("generated_pdfs", []),
                "packet_path": pdf_result.get("packet_path"),
                "errors": pdf_result.get("errors", [])
            }
        else:
            # Return missing fields
            missing_info = await chat_to_pdf_service.get_missing_information(
                db,
                request.session_id
            )

            return {
                "success": True,
                "workflow_complete": False,
                "motion_id": prepare_result["motion_id"],
                "missing_fields": prepare_result.get("missing_fields", []),
                "missing_questions": missing_info,
                "message": "Additional information needed to complete forms"
            }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error in workflow: {str(e)}"
        )