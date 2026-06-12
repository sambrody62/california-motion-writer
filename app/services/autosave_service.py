"""
Auto-save service for chat messages and form data
Automatically saves user progress to prevent data loss
"""
import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.models.database import ChatSession, ChatMessage, Motion
from app.core.database import get_db

logger = logging.getLogger(__name__)


class AutoSaveService:
    """Service for automatic saving of user data during chat sessions"""

    def __init__(self):
        self.save_interval = 30  # seconds
        self.pending_saves = {}  # session_id -> data
        self.save_tasks = {}  # session_id -> task

    async def start_auto_save(self, session_id: str):
        """Start auto-save for a chat session"""
        if session_id in self.save_tasks:
            logger.debug(f"Auto-save already running for session {session_id}")
            return

        task = asyncio.create_task(self._auto_save_loop(session_id))
        self.save_tasks[session_id] = task
        logger.info(f"Started auto-save for session {session_id}")

    async def stop_auto_save(self, session_id: str):
        """Stop auto-save for a chat session"""
        if session_id in self.save_tasks:
            self.save_tasks[session_id].cancel()
            del self.save_tasks[session_id]

            # Perform final save
            await self._save_session_data(session_id)
            logger.info(f"Stopped auto-save for session {session_id}")

    async def queue_save(self, session_id: str, data: Dict[str, Any]):
        """Queue data for auto-saving"""
        if session_id not in self.pending_saves:
            self.pending_saves[session_id] = {}

        self.pending_saves[session_id].update(data)
        self.pending_saves[session_id]['last_modified'] = datetime.utcnow().isoformat()

    async def save_message(self, session_id: str, message: Dict[str, Any]):
        """Save a single chat message immediately"""
        try:
            async with get_db() as db:
                # Create message record
                new_message = ChatMessage(
                    session_id=session_id,
                    content=message.get('content', ''),
                    sender=message.get('sender', 'user'),
                    message_type=message.get('type', 'text'),
                    metadata=json.dumps(message.get('metadata', {}))
                )
                db.add(new_message)

                # Update session last activity
                await db.execute(
                    update(ChatSession)
                    .where(ChatSession.session_id == session_id)
                    .values(last_activity=datetime.utcnow())
                )

                await db.commit()
                logger.debug(f"Saved message for session {session_id}")

                return {
                    'success': True,
                    'message_id': new_message.id
                }

        except Exception as e:
            logger.error(f"Error saving message: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    async def save_form_progress(self, session_id: str, form_data: Dict[str, Any]):
        """Save form progress data"""
        try:
            async with get_db() as db:
                # Get or create motion record
                result = await db.execute(
                    select(Motion)
                    .where(Motion.session_id == session_id)
                    .order_by(Motion.created_at.desc())
                    .limit(1)
                )
                motion = result.scalar_one_or_none()

                if motion:
                    # Update existing motion
                    motion.form_data = json.dumps(form_data)
                    motion.updated_at = datetime.utcnow()
                else:
                    # Create new motion
                    motion = Motion(
                        session_id=session_id,
                        motion_type=form_data.get('motion_type', 'unknown'),
                        status='draft',
                        form_data=json.dumps(form_data)
                    )
                    db.add(motion)

                await db.commit()
                logger.debug(f"Saved form progress for session {session_id}")

                return {
                    'success': True,
                    'motion_id': motion.id
                }

        except Exception as e:
            logger.error(f"Error saving form progress: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    async def _auto_save_loop(self, session_id: str):
        """Background task for auto-saving"""
        try:
            while True:
                await asyncio.sleep(self.save_interval)
                await self._save_session_data(session_id)

        except asyncio.CancelledError:
            logger.debug(f"Auto-save loop cancelled for session {session_id}")
            raise
        except Exception as e:
            logger.error(f"Error in auto-save loop: {e}")

    async def _save_session_data(self, session_id: str):
        """Save pending session data"""
        if session_id not in self.pending_saves:
            return

        data = self.pending_saves.get(session_id, {})
        if not data:
            return

        try:
            async with get_db() as db:
                # Update session context
                result = await db.execute(
                    select(ChatSession).where(ChatSession.session_id == session_id)
                )
                session = result.scalar_one_or_none()

                if session:
                    # Merge context data
                    context = json.loads(session.context) if session.context else {}
                    context.update(data)

                    session.context = json.dumps(context)
                    session.last_activity = datetime.utcnow()

                    await db.commit()
                    logger.debug(f"Auto-saved data for session {session_id}")

                    # Clear pending saves
                    del self.pending_saves[session_id]

        except Exception as e:
            logger.error(f"Error in auto-save: {e}")

    async def recover_session(self, session_id: str) -> Dict[str, Any]:
        """Recover auto-saved session data"""
        try:
            async with get_db() as db:
                # Get session
                result = await db.execute(
                    select(ChatSession).where(ChatSession.session_id == session_id)
                )
                session = result.scalar_one_or_none()

                if not session:
                    return {
                        'success': False,
                        'error': 'Session not found'
                    }

                # Get messages
                messages_result = await db.execute(
                    select(ChatMessage)
                    .where(ChatMessage.session_id == session_id)
                    .order_by(ChatMessage.created_at)
                )
                messages = messages_result.scalars().all()

                # Get latest motion data
                motion_result = await db.execute(
                    select(Motion)
                    .where(Motion.session_id == session_id)
                    .order_by(Motion.created_at.desc())
                    .limit(1)
                )
                motion = motion_result.scalar_one_or_none()

                return {
                    'success': True,
                    'session': {
                        'id': session.session_id,
                        'state': session.state,
                        'context': json.loads(session.context) if session.context else {},
                        'last_activity': session.last_activity.isoformat() if session.last_activity else None
                    },
                    'messages': [
                        {
                            'id': msg.id,
                            'content': msg.content,
                            'sender': msg.sender,
                            'type': msg.message_type,
                            'metadata': json.loads(msg.metadata) if msg.metadata else {},
                            'timestamp': msg.created_at.isoformat()
                        }
                        for msg in messages
                    ],
                    'form_data': json.loads(motion.form_data) if motion and motion.form_data else {}
                }

        except Exception as e:
            logger.error(f"Error recovering session: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    async def cleanup_old_saves(self, days: int = 30):
        """Clean up old auto-saved data"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)

            async with get_db() as db:
                # Delete old draft motions
                await db.execute(
                    Motion.__table__.delete()
                    .where(Motion.status == 'draft')
                    .where(Motion.updated_at < cutoff_date)
                )

                # Delete old inactive sessions
                await db.execute(
                    ChatSession.__table__.delete()
                    .where(ChatSession.last_activity < cutoff_date)
                )

                await db.commit()
                logger.info(f"Cleaned up auto-saved data older than {days} days")

        except Exception as e:
            logger.error(f"Error cleaning up old saves: {e}")


# Singleton instance
auto_save_service = AutoSaveService()