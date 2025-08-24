"""
Database configuration and connection management
"""
import logging
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from app.core.config import settings

try:
    from google.cloud import secretmanager
    HAS_GCP = True
except ImportError:
    HAS_GCP = False

logger = logging.getLogger(__name__)

Base = declarative_base()

class Database:
    def __init__(self):
        self.engine = None
        self.async_session = None
    
    async def get_db_password(self) -> str:
        """Retrieve database password from Secret Manager"""
        if not HAS_GCP:
            return "SecurePassword123!"
        
        try:
            client = secretmanager.SecretManagerServiceClient()
            name = f"projects/{settings.PROJECT_ID}/secrets/{settings.DB_PASSWORD_SECRET}/versions/latest"
            response = client.access_secret_version(request={"name": name})
            return response.payload.data.decode("UTF-8")
        except Exception as e:
            logger.error(f"Failed to retrieve database password: {e}")
            # Fallback for local development
            return "SecurePassword123!"
    
    async def init(self):
        """Initialize database connection"""
        
        # Build connection string
        if settings.ENVIRONMENT == "development":
            # Use SQLite for local development
            DATABASE_URL = "sqlite+aiosqlite:///./test.db"
        elif settings.ENVIRONMENT == "production":
            password = await self.get_db_password()
            # Use Cloud SQL connector for production
            DATABASE_URL = (
                f"postgresql+asyncpg://{settings.DB_USER}:{password}@/"
                f"{settings.DB_NAME}?host={settings.DB_HOST}"
            )
        else:
            password = await self.get_db_password()
            # Direct connection for development
            DATABASE_URL = (
                f"postgresql+asyncpg://{settings.DB_USER}:{password}@"
                f"localhost:5432/{settings.DB_NAME}"
            )
        
        # Create async engine
        self.engine = create_async_engine(
            DATABASE_URL,
            echo=True if settings.ENVIRONMENT == "development" else False,
            pool_size=20,
            max_overflow=40,
            pool_pre_ping=True,
        )
        
        # Create session factory
        self.async_session = async_sessionmaker(
            self.engine, 
            class_=AsyncSession, 
            expire_on_commit=False
        )
        
        logger.info("Database connection initialized")
    
    async def create_tables(self):
        """Create all tables"""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get database session"""
        async with self.async_session() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

# Global database instance
db = Database()

async def init_db():
    """Initialize database on startup"""
    await db.init()
    # Optionally create tables (for development)
    if settings.ENVIRONMENT == "development":
        await db.create_tables()

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to get database session"""
    async for session in db.get_session():
        yield session