"""
FastAPI main application
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import os

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.database import Base, db, init_db
from app.core.deps import get_current_user_ws
from app.services.chat_service import chat_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize application on startup"""
    logger.info("Starting California Motion Writer API")
    # Initialize database
    await init_db()
    yield
    # Cleanup
    logger.info("Shutting down California Motion Writer API")

# Create FastAPI app
app = FastAPI(
    title="California Motion Writer API",
    description="API for generating California family court motions with chat support",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    # Comma-separated env var so each environment (Vercel prod, localhost dev)
    # sets its own origins without a code change
    allow_origins=[
        origin.strip()
        for origin in os.getenv(
            "CORS_ORIGINS",
            "http://localhost:3000,http://localhost:3001,http://127.0.0.1:3000",
        ).split(",")
        if origin.strip()
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api/v1")

# Health check endpoint
@app.get("/health")
async def health_check():
    """Simple health check endpoint"""
    return {"status": "healthy", "service": "California Motion Writer API"}

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "California Motion Writer API",
        "documentation": "/docs",
        "health": "/health"
    }

# WebSocket endpoint for chat
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time chat"""
    await websocket.accept()
    user_id = None
    session_id = None

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()

            # Handle different message types
            message_type = data.get("type")

            if message_type == "connect":
                # Authenticate user via JWT
                token = data.get("data", {}).get("token")
                if not token:
                    await websocket.close(code=1008)
                    return
                from app.core.database import get_db_sync
                ws_db = get_db_sync()
                user = await get_current_user_ws(token, ws_db)
                if user is None:
                    await websocket.close(code=1008)
                    return
                user_id = str(user.id)

                await websocket.send_json({
                    "type": "connected",
                    "data": {"message": "Connected to chat service"}
                })

            elif message_type == "message" and user_id:
                # Process chat message
                content = data.get("data", {}).get("content", "")

                if not session_id:
                    # Create new session if needed
                    from app.core.database import get_db_sync
                    from app.services.chat_service import chat_service

                    db = get_db_sync()
                    result = await chat_service.create_session(
                        db, user_id, initial_message=content
                    )
                    session_id = result["session_id"]

                # Process message
                response = await chat_service.process_message(
                    db, session_id, user_id, content
                )

                # Send response back to client
                await websocket.send_json({
                    "type": "message",
                    "data": {
                        "content": response["response"]["message"]["content"],
                        "quick_replies": response["response"].get("quick_replies", []),
                        "session_id": session_id
                    }
                })

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for user {user_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)