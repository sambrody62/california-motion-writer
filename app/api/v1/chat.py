"""
Chat API endpoints for conversation management
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, UUID4
from datetime import datetime

from app.core.deps import get_db, get_current_user
from app.models.user import User
from app.services.chat_service import ChatService
from app.models.chat import ChatSessionStatus, ChatSessionState

router = APIRouter(tags=["chat"])

# Request/Response models
class CreateSessionRequest(BaseModel):
    initial_message: Optional[str] = None

class CreateSessionResponse(BaseModel):
    session_id: str
    status: str
    state: str
    created_at: datetime

class SendMessageRequest(BaseModel):
    session_id: str
    content: str

class SendMessageResponse(BaseModel):
    success: bool
    message_id: Optional[str] = None
    response: Optional[dict] = None
    error: Optional[str] = None

class SessionListResponse(BaseModel):
    sessions: List[dict]

class MessageHistoryResponse(BaseModel):
    session_id: str
    messages: List[dict]
    total_count: int

class UpdateSessionStateRequest(BaseModel):
    state: ChatSessionState
    context: Optional[dict] = None

# Initialize service
chat_service = ChatService()

@router.post("/sessions", response_model=CreateSessionResponse, status_code=201)
async def create_chat_session(
    request: CreateSessionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> CreateSessionResponse:
    """
    Create a new chat session for the current user
    """
    try:
        session = await chat_service.create_session(
            db,
            str(current_user.id),
            initial_message=request.initial_message
        )

        return CreateSessionResponse(
            session_id=str(session.id),
            status=session.status.value,
            state=session.current_state.value,
            created_at=session.started_at
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create session: {str(e)}"
        )

@router.get("/sessions", response_model=SessionListResponse)
async def get_active_sessions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> SessionListResponse:
    """
    Get all active chat sessions for the current user
    """
    try:
        sessions = await chat_service.get_active_sessions(db, str(current_user.id))

        session_list = [
            {
                "id": str(session.id),
                "status": session.status.value,
                "state": session.current_state.value,
                "started_at": session.started_at.isoformat(),
                "last_message_at": session.last_message_at.isoformat() if session.last_message_at else None,
                "intent": session.intent,
                "motion_type": session.motion_type_detected
            }
            for session in sessions
        ]

        return SessionListResponse(sessions=session_list)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get sessions: {str(e)}"
        )

@router.get("/sessions/{session_id}/messages", response_model=MessageHistoryResponse)
async def get_message_history(
    session_id: str,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> MessageHistoryResponse:
    """
    Get message history for a specific session
    """
    try:
        # Verify session belongs to user
        from sqlalchemy import select
        from app.models.chat import ChatSession

        stmt = select(ChatSession).where(
            ChatSession.id == session_id,
            ChatSession.user_id == str(current_user.id)
        )
        result = await db.execute(stmt)
        session = result.scalar_one_or_none()

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )

        messages = await chat_service.get_session_history(db, session_id, limit)

        return MessageHistoryResponse(
            session_id=session_id,
            messages=messages,
            total_count=len(messages)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get message history: {str(e)}"
        )

@router.post("/messages", response_model=SendMessageResponse)
async def send_message(
    request: SendMessageRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> SendMessageResponse:
    """
    Send a message in a chat session (REST alternative to WebSocket)
    """
    try:
        # Verify session belongs to user
        from sqlalchemy import select
        from app.models.chat import ChatSession

        import uuid
        # Convert session_id to UUID if it's a string
        session_uuid = uuid.UUID(request.session_id) if isinstance(request.session_id, str) else request.session_id
        # Handle UUID comparison for SQLite
        user_id_for_query = str(current_user.id) if hasattr(current_user.id, 'hex') else current_user.id

        stmt = select(ChatSession).where(
            ChatSession.id == str(session_uuid),
            ChatSession.user_id == user_id_for_query
        )
        result = await db.execute(stmt)
        session = result.scalar_one_or_none()

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )

        # Process the message
        result = await chat_service.process_user_message(
            db,
            str(request.session_id),
            request.content,
            str(current_user.id)
        )

        if result["success"]:
            return SendMessageResponse(
                success=True,
                message_id=result["message"]["id"],
                response=result
            )
        else:
            return SendMessageResponse(
                success=False,
                error=result.get("error", "Processing failed")
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process message: {str(e)}"
        )

@router.put("/sessions/{session_id}/state")
async def update_session_state(
    session_id: str,
    request: UpdateSessionStateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> dict:
    """
    Update the state of a chat session
    """
    try:
        from sqlalchemy import select
        from app.models.chat import ChatSession

        stmt = select(ChatSession).where(
            ChatSession.id == session_id,
            ChatSession.user_id == str(current_user.id)
        )
        result = await db.execute(stmt)
        session = result.scalar_one_or_none()

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )

        # Update session state
        session.current_state = request.state
        if request.context:
            session.context = {**session.context, **request.context}

        await db.commit()

        return {
            "success": True,
            "session_id": session_id,
            "new_state": session.current_state.value,
            "context": session.context
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update session state: {str(e)}"
        )

@router.post("/sessions/{session_id}/complete")
async def complete_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> dict:
    """
    Mark a chat session as completed
    """
    try:
        from sqlalchemy import select
        from app.models.chat import ChatSession

        stmt = select(ChatSession).where(
            ChatSession.id == session_id,
            ChatSession.user_id == str(current_user.id)
        )
        result = await db.execute(stmt)
        session = result.scalar_one_or_none()

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )

        success = await chat_service.complete_session(db, session_id)

        return {
            "success": success,
            "session_id": session_id,
            "status": "completed" if success else "failed"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to complete session: {str(e)}"
        )

@router.get("/sessions/{session_id}")
async def get_session_details(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> dict:
    """
    Get detailed information about a specific session
    """
    try:
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        from app.models.chat import ChatSession

        import uuid
        # Convert session_id to UUID if it's a string
        session_uuid = uuid.UUID(session_id) if isinstance(session_id, str) else session_id
        # Handle UUID comparison for SQLite
        user_id_for_query = str(current_user.id) if hasattr(current_user.id, 'hex') else current_user.id

        stmt = select(ChatSession).options(
            selectinload(ChatSession.messages)
        ).where(
            ChatSession.id == str(session_uuid),
            ChatSession.user_id == user_id_for_query
        )
        result = await db.execute(stmt)
        session = result.scalar_one_or_none()

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )

        return {
            "id": str(session.id),
            "status": session.status.value,
            "state": session.current_state.value,
            "started_at": session.started_at.isoformat(),
            "last_message_at": session.last_message_at.isoformat() if session.last_message_at else None,
            "completed_at": session.completed_at.isoformat() if session.completed_at else None,
            "intent": session.intent,
            "confidence_score": session.confidence_score,
            "motion_type": session.motion_type_detected,
            "forms_identified": session.forms_identified,
            "context": session.context,
            "message_count": len(session.messages),
            "motion_id": str(session.motion_id) if session.motion_id else None
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get session details: {str(e)}"
        )