#!/usr/bin/env python3
"""
Simple development server runner
"""
import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

async def init_database():
    """Initialize database tables"""
    from app.core.database import database, Base
    from app.models import user, motion  # Import models to register them
    
    print("Initializing database...")
    await database.init()
    
    # Create tables for SQLite
    if os.getenv("ENVIRONMENT", "development") == "development":
        async with database.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    
    print("Database initialized!")

async def main():
    """Main entry point"""
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Initialize database
    await init_database()
    
    # Start the server
    print("\n" + "="*50)
    print("🚀 California Motion Writer - Development Server")
    print("="*50)
    print("📍 Local URL: http://localhost:8080")
    print("📚 API Docs: http://localhost:8080/docs")
    print("🏠 Homepage: http://localhost:8080")
    print("\nPress Ctrl+C to stop the server")
    print("="*50 + "\n")
    
    # Run the FastAPI app
    import uvicorn
    from main import app
    
    config = uvicorn.Config(
        app=app,
        host="0.0.0.0",
        port=8080,
        reload=True,
        log_level="info"
    )
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nServer stopped.")
        sys.exit(0)