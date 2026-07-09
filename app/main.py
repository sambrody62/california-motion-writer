"""
FastAPI main application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import os

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.database import Base, db, init_db
from app.middleware.rate_limiter import rate_limit_middleware

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

# Rate limiting on expensive routes (LLM, PDF, auth) — see RATE_LIMITS
app.middleware("http")(rate_limit_middleware)

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)