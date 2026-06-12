"""
WebSocket handler for real-time chat communication
"""
import json
import logging
from typing import Dict, Set, Optional
from fastapi import WebSocket, WebSocketDisconnect, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio
from datetime import datetime

from app.core.deps import get_db, get_current_user_ws
from app.services.chat_service import ChatService
from app.models.user import User

logger = logging.getLogger(__name__)

class ConnectionManager:
    """Manage WebSocket connections for chat sessions"""

    def __init__(self):
        # Track active connections by user_id
        self.active_connections: Dict[str, WebSocket] = {}
        # Track session_id for each user
        self.user_sessions: Dict[str, str] = {}
        self.chat_service = ChatService()

    async def connect(self, websocket: WebSocket, user_id: str, session_id: Optional[str] = None):
        """Accept and register a new WebSocket connection"""
        await websocket.accept()

        # Close existing connection if user reconnects
        if user_id in self.active_connections:
            old_ws = self.active_connections[user_id]
            try:
                await old_ws.close()
            except:
                pass

        self.active_connections[user_id] = websocket
        if session_id:
            self.user_sessions[user_id] = session_id

        logger.info(f"WebSocket connected: user={user_id}, session={session_id}")

    def disconnect(self, user_id: str):
        """Remove a WebSocket connection"""
        if user_id in self.active_connections:
            del self.active_connections[user_id]
        if user_id in self.user_sessions:
            del self.user_sessions[user_id]
        logger.info(f"WebSocket disconnected: user={user_id}")

    async def send_message(self, user_id: str, message: dict):
        """Send a message to a specific user"""
        if user_id in self.active_connections:
            websocket = self.active_connections[user_id]
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error sending message to {user_id}: {e}")
                # Remove dead connection
                self.disconnect(user_id)

    async def broadcast_to_session(self, session_id: str, message: dict, exclude_user: Optional[str] = None):
        """Broadcast message to all users in a session (future: multi-user support)"""
        for user_id, sess_id in self.user_sessions.items():
            if sess_id == session_id and user_id != exclude_user:
                await self.send_message(user_id, message)

# Global connection manager instance
manager = ConnectionManager()

async def websocket_endpoint(
    websocket: WebSocket,
    db: AsyncSession = Depends(get_db)
):
    """
    Main WebSocket endpoint for chat communication

    Expected message format:
    {
        "type": "connect" | "message" | "typing" | "session_update",
        "data": {
            "token": "jwt_token" (for connect),
            "session_id": "uuid" (optional for connect),
            "content": "message text" (for message),
            "state": "typing" | "idle" (for typing)
        }
    }
    """
    user = None
    user_id = None
    session_id = None

    try:
        # Wait for authentication message
        auth_message = await websocket.receive_json()

        if auth_message.get("type") != "connect":
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        # Authenticate user from token
        token = auth_message.get("data", {}).get("token")
        if not token:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        # Get user from token (implement actual JWT verification)
        user = await get_current_user_ws(token, db)
        if not user:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        user_id = str(user.id)
        session_id = auth_message.get("data", {}).get("session_id")

        # Connect the WebSocket
        await manager.connect(websocket, user_id, session_id)

        # Send connection success
        await websocket.send_json({
            "type": "connected",
            "data": {
                "user_id": user_id,
                "session_id": session_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        })

        # Create or resume chat session if not provided
        if not session_id:
            session = await manager.chat_service.create_session(db, user_id)
            session_id = str(session.id)
            manager.user_sessions[user_id] = session_id

            # Send session created message
            await websocket.send_json({
                "type": "session_created",
                "data": {
                    "session_id": session_id,
                    "state": session.current_state.value
                }
            })

        # Handle messages
        while True:
            try:
                # Receive message from client
                message = await websocket.receive_json()
                message_type = message.get("type")
                data = message.get("data", {})

                if message_type == "message":
                    # Process user message
                    content = data.get("content")
                    if content:
                        # Send typing indicator
                        await websocket.send_json({
                            "type": "assistant_typing",
                            "data": {"typing": True}
                        })

                        # Process message through chat service
                        result = await manager.chat_service.process_user_message(
                            db, session_id, content, user_id
                        )

                        # Stop typing indicator
                        await websocket.send_json({
                            "type": "assistant_typing",
                            "data": {"typing": False}
                        })

                        # Send response
                        if result["success"]:
                            await websocket.send_json({
                                "type": "message",
                                "data": result["message"]
                            })

                            # Send session update if state changed
                            await websocket.send_json({
                                "type": "session_update",
                                "data": result["session"]
                            })
                        else:
                            await websocket.send_json({
                                "type": "error",
                                "data": {
                                    "error": result.get("error", "Processing failed")
                                }
                            })

                elif message_type == "typing":
                    # Handle typing indicator from client
                    typing_state = data.get("state", "idle")
                    # Could broadcast to other participants in future
                    logger.debug(f"User {user_id} typing: {typing_state}")

                elif message_type == "get_history":
                    # Fetch and send message history
                    history = await manager.chat_service.get_session_history(
                        db, session_id, limit=50
                    )
                    await websocket.send_json({
                        "type": "history",
                        "data": {"messages": history}
                    })

                elif message_type == "ping":
                    # Heartbeat to keep connection alive
                    await websocket.send_json({
                        "type": "pong",
                        "data": {"timestamp": datetime.utcnow().isoformat()}
                    })

            except WebSocketDisconnect:
                break
            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "data": {"error": "Invalid message format"}
                })
            except Exception as e:
                logger.error(f"WebSocket error for user {user_id}: {e}")
                await websocket.send_json({
                    "type": "error",
                    "data": {"error": "Internal server error"}
                })

    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
    finally:
        if user_id:
            manager.disconnect(user_id)
            logger.info(f"WebSocket closed for user {user_id}")

# Export for use in routes
__all__ = ['websocket_endpoint', 'manager']