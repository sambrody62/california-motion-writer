"""
FastAPI main application for local development
"""
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

# Load development environment
from dotenv import load_dotenv
load_dotenv('.env.development')

from app.api.v1.router import api_router
from app.core.database_local import Base, engine, get_db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize application on startup"""
    logger.info("Starting California Motion Writer API (Local Development)")

    # Create database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    logger.info("Database tables created")
    yield

    # Cleanup
    logger.info("Shutting down California Motion Writer API")

# Create FastAPI app
app = FastAPI(
    title="California Motion Writer API (Local)",
    description="Local development API for California family court motions",
    version="1.0.0-dev",
    lifespan=lifespan
)

# Configure CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins in development
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
    return {"status": "healthy", "service": "California Motion Writer API", "environment": "development"}

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "California Motion Writer API (Local Development)",
        "documentation": "/docs",
        "health": "/health",
        "environment": "development"
    }

# Simplified WebSocket endpoint for testing
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Simplified WebSocket endpoint for testing"""
    await websocket.accept()

    try:
        await websocket.send_json({
            "type": "connected",
            "data": {"message": "Connected to chat service (test mode)"}
        })

        while True:
            # Receive and echo messages for testing
            data = await websocket.receive_json()

            if data.get("type") == "message":
                content = data.get("data", {}).get("content", "")

                # Simple echo response for testing
                await websocket.send_json({
                    "type": "message",
                    "data": {
                        "content": f"Echo: {content}",
                        "session_id": "test-session-123"
                    }
                })

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)