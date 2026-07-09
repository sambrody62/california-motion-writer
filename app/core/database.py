"""
Database configuration and connection management
"""
import os
import logging
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base

# Conditionally import GCP services
USE_GCP = os.getenv("USE_GCP", "true").lower() == "true"
if USE_GCP:
    try:
        from google.cloud import secretmanager
    except ImportError:
        USE_GCP = False

from app.core.config import settings

logger = logging.getLogger(__name__)

Base = declarative_base()


def _sql_echo_enabled() -> bool:
    """SQL echo prints bound parameters (names, case details) — explicit opt-in only."""
    return os.getenv("SQL_ECHO", "false").lower() == "true"


def _normalize_database_url(url: str) -> str:
    """Ensure postgres URLs use the asyncpg driver (Supabase/Render give postgres://)."""
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+asyncpg://", 1)
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


def _connect_args_for(url: str) -> dict:
    # Supabase pooler (pgBouncer transaction mode, port 6543) can't use
    # asyncpg's prepared-statement cache; direct connections (5432) can.
    if ":6543" in url:
        return {"statement_cache_size": 0}
    return {}


class Database:
    def __init__(self):
        self.engine = None
        self.async_session = None
    
    async def get_db_password(self) -> str:
        """Retrieve database password from Secret Manager"""
        # For local development with SQLite, return dummy password
        if settings.ENVIRONMENT == "development" and not USE_GCP:
            return "local-dev-password"

        try:
            client = secretmanager.SecretManagerServiceClient()
            name = f"projects/{settings.PROJECT_ID}/secrets/{settings.DB_PASSWORD_SECRET}/versions/latest"
            response = client.access_secret_version(request={"name": name})
            return response.payload.data.decode("UTF-8")
        except Exception as e:
            logger.error(f"Failed to retrieve database password: {e}")

            # Only allow fallback in development with explicit env variable
            if settings.ENVIRONMENT == "development":
                import os
                local_password = os.getenv("LOCAL_DB_PASSWORD", "local-dev-password")
                logger.warning("Using LOCAL_DB_PASSWORD for development")
                return local_password
            else:
                # Never fallback in production - fail fast
                raise Exception(
                    f"Cannot retrieve database password from Secret Manager: {e}"
                )
    
    async def init(self):
        """Initialize database connection"""
        env_url = os.getenv("DATABASE_URL")
        use_local_db = os.getenv("USE_LOCAL_DATABASE", "false").lower() == "true"
        if env_url:
            # Explicit connection string (Supabase/Render path) wins over everything
            DATABASE_URL = _normalize_database_url(env_url)
        elif settings.ENVIRONMENT == "development" and (use_local_db or not USE_GCP):
            DATABASE_URL = "sqlite+aiosqlite:///./local.db"
        else:
            password = await self.get_db_password()

            # Build connection string
            if settings.ENVIRONMENT == "production":
                # Use Cloud SQL connector for production
                DATABASE_URL = (
                    f"postgresql+asyncpg://{settings.DB_USER}:{password}@/"
                    f"{settings.DB_NAME}?host={settings.DB_HOST}"
                )
            else:
                # Direct connection for development
                DATABASE_URL = (
                    f"postgresql+asyncpg://{settings.DB_USER}:{password}@"
                    f"localhost:5432/{settings.DB_NAME}"
                )
        
        # Create async engine (pool sized for Supabase free tier via env; GCP defaults preserved)
        engine_kwargs = {
            "echo": _sql_echo_enabled(),
            "pool_pre_ping": True,
        }
        if not DATABASE_URL.startswith("sqlite"):
            # SQLite's StaticPool rejects pool sizing arguments
            engine_kwargs["pool_size"] = int(os.getenv("DB_POOL_SIZE", "20"))
            engine_kwargs["max_overflow"] = int(os.getenv("DB_MAX_OVERFLOW", "40"))
            engine_kwargs["connect_args"] = _connect_args_for(DATABASE_URL)
        self.engine = create_async_engine(DATABASE_URL, **engine_kwargs)
        
        # Create session factory
        self.async_session = async_sessionmaker(
            self.engine, 
            class_=AsyncSession, 
            expire_on_commit=False
        )
        
        logger.info("Database connection initialized")
    
    async def create_tables(self):
        """Create all tables (idempotent, race-tolerant across workers)"""
        from sqlalchemy.exc import OperationalError, ProgrammingError

        try:
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
        except (OperationalError, ProgrammingError) as exc:
            # With multiple uvicorn workers, both can pass create_all's
            # existence check and race the CREATE; the loser's error means
            # the tables exist, which is the outcome we wanted.
            if "already exists" in str(exc).lower():
                logger.info("Tables already created by a concurrent worker")
            else:
                raise
    
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
    # create_all is idempotent (checkfirst) — required for first boot against
    # a fresh Supabase database; no Alembic in this project
    await db.create_tables()

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to get database session"""
    async for session in db.get_session():
        yield session