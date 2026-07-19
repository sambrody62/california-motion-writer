"""
Pytest configuration and fixtures
"""
import os
import sys
import pytest
import pytest_asyncio
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

# Set test environment
os.environ["ENVIRONMENT"] = "test"
os.environ["USE_GCP"] = "false"
os.environ["USE_MOCK_LLM"] = "true"
os.environ["SECRET_KEY"] = "test-secret-key-for-testing"
# Off by default: the shared-IP auth fixture would trip auth limits mid-suite
os.environ["RATE_LIMIT_ENABLED"] = "false"
# Off by default: billing gate would 402 the existing LLM/PDF tests
os.environ["BILLING_ENABLED"] = "false"

# Add app to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app
from app.core.database import Base, get_db

# Import all models to ensure they're registered with Base
from app.models.user import User
from app.models.profile import Profile
from app.models.motion import Motion
from app.models.chat import ChatSession, ChatMessage
from app.models.evidence import Evidence
from app.models.subscription import Subscription

from app.api.v1.endpoints.auth import get_password_hash

@pytest_asyncio.fixture(scope="function")
async def test_db():
    """Create a test database for each test function."""
    # Create test engine with in-memory SQLite
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        future=True
    )

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session
    async_session = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    async with async_session() as session:
        yield session
        await session.close()

    # Clean up
    await engine.dispose()

@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Create a test client for the FastAPI app."""

    # Create test database
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        future=True
    )

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session factory
    async_session_maker = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    # Override the dependency
    async def override_get_db():
        async with async_session_maker() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    # Create client
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test", follow_redirects=True) as ac:
        yield ac

    # Clean up
    app.dependency_overrides.clear()
    await engine.dispose()

@pytest_asyncio.fixture
async def client_with_db():
    """Client plus a session maker into the same in-memory DB, for tests that
    must insert rows (e.g. subscriptions) for API-registered users."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        future=True
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_maker = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    async def override_get_db():
        async with session_maker() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac, session_maker
    app.dependency_overrides.clear()
    await engine.dispose()

@pytest_asyncio.fixture
async def test_user(test_db: AsyncSession) -> User:
    """Create a test user."""
    user = User(
        email="test@example.com",
        password_hash=get_password_hash("testpass123"),
        full_name="Test User",
        phone="123-456-7890",
        is_active=True,
        email_verified=True
    )
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)
    return user

@pytest_asyncio.fixture
async def auth_headers(client: AsyncClient) -> dict:
    """Get authentication headers for a test user."""
    # Register a user
    register_data = {
        "email": "auth@example.com",
        "password": "authpass123",
        "full_name": "Auth User",
        "phone": "987-654-3210"
    }
    await client.post("/api/v1/auth/register", json=register_data)

    # Login to get token
    login_data = {
        "username": "auth@example.com",
        "password": "authpass123"
    }
    response = await client.post(
        "/api/v1/auth/token",
        data=login_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    token = response.json()["access_token"]

    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def sample_motion_data():
    """Sample motion data for testing."""
    return {
        "motion_type": "RFO",
        "title": "Request for Order - Custody",
        "description": "Request for custody modification",
        "case_caption": "Smith v. Smith",
        "filing_track": "standard",
        "courthouse": "Los Angeles Superior Court",
        "intake_data": {
            "reason": "Change in circumstances",
            "children_involved": True
        }
    }

@pytest.fixture
def sample_profile_data():
    """Sample profile data for testing."""
    return {
        "case_number": "FL-2024-001",
        "county": "Los Angeles",
        "court_branch": "Stanley Mosk Courthouse",
        "department": "Dept. 1",
        "is_petitioner": True,
        "party_name": "John Smith",
        "party_address": "123 Main St, Los Angeles, CA 90001",
        "party_phone": "555-123-4567",
        "other_party_name": "Jane Smith",
        "other_party_address": "456 Oak Ave, Los Angeles, CA 90002",
        "children_info": [
            {
                "name": "Child Smith",
                "birthdate": "2015-01-01",
                "ssn_last_4": "1234"
            }
        ]
    }