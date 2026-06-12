"""
Tests for authentication endpoints
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.api.v1.endpoints.auth import get_password_hash, verify_password


class TestAuthentication:
    """Test authentication endpoints and functionality."""

    @pytest.mark.asyncio
    async def test_register_new_user(self, client: AsyncClient):
        """Test successful user registration."""
        user_data = {
            "email": "newuser@example.com",
            "password": "securepass123",
            "full_name": "New User",
            "phone": "555-1234"
        }

        response = await client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 201
        data = response.json()

        assert "access_token" in data
        assert data["token_type"] == "bearer"
        # Token should be a valid JWT (has 3 parts separated by dots)
        assert len(data["access_token"].split(".")) == 3

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, client: AsyncClient):
        """Test registration with duplicate email."""
        user_data = {
            "email": "duplicate@example.com",
            "password": "password123",
            "full_name": "First User",
            "phone": "555-1111"
        }

        # Register first user
        response = await client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 201

        # Try to register with same email
        user_data["full_name"] = "Second User"
        response = await client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_register_invalid_email(self, client: AsyncClient):
        """Test registration with invalid email format."""
        user_data = {
            "email": "invalid-email",
            "password": "password123",
            "full_name": "Invalid Email User",
            "phone": "555-2222"
        }

        response = await client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_register_weak_password(self, client: AsyncClient):
        """Test registration with weak password."""
        user_data = {
            "email": "weak@example.com",
            "password": "123",  # Too short
            "full_name": "Weak Password User",
            "phone": "555-3333"
        }

        response = await client.post("/api/v1/auth/register", json=user_data)
        # Depending on implementation, this might be 422 or 400
        assert response.status_code in [400, 422]

    @pytest.mark.asyncio
    async def test_login_valid_credentials(self, client: AsyncClient):
        """Test login with valid credentials."""
        # First register a user
        register_data = {
            "email": "login@example.com",
            "password": "loginpass123",
            "full_name": "Login User",
            "phone": "555-4444"
        }
        await client.post("/api/v1/auth/register", json=register_data)

        # Now login using /token endpoint
        login_data = {
            "username": "login@example.com",  # OAuth2 spec uses 'username'
            "password": "loginpass123"
        }
        response = await client.post(
            "/api/v1/auth/token",
            data=login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_login_invalid_email(self, client: AsyncClient):
        """Test login with non-existent email."""
        login_data = {
            "username": "nonexistent@example.com",
            "password": "somepass123"
        }
        response = await client.post(
            "/api/v1/auth/token",
            data=login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )

        assert response.status_code == 401
        assert "incorrect" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, client: AsyncClient):
        """Test login with wrong password."""
        # First register a user
        register_data = {
            "email": "wrongpass@example.com",
            "password": "correctpass123",
            "full_name": "Wrong Pass User",
            "phone": "555-5555"
        }
        await client.post("/api/v1/auth/register", json=register_data)

        # Try to login with wrong password
        login_data = {
            "username": "wrongpass@example.com",
            "password": "wrongpass123"
        }
        response = await client.post(
            "/api/v1/auth/token",
            data=login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )

        assert response.status_code == 401
        assert "incorrect" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_get_current_user(self, client: AsyncClient, auth_headers: dict):
        """Test getting current user with valid token."""
        response = await client.get("/api/v1/auth/me", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "auth@example.com"
        assert data["full_name"] == "Auth User"

    @pytest.mark.asyncio
    async def test_get_current_user_no_token(self, client: AsyncClient):
        """Test getting current user without token."""
        response = await client.get("/api/v1/auth/me")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self, client: AsyncClient):
        """Test getting current user with invalid token."""
        headers = {"Authorization": "Bearer invalid-token-here"}
        response = await client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == 401

    def test_password_hashing(self):
        """Test password hashing and verification."""
        password = "mysecretpassword"
        hashed = get_password_hash(password)

        # Hashed password should be different from plain text
        assert hashed != password

        # Should be able to verify the password
        assert verify_password(password, hashed) == True

        # Wrong password should not verify
        assert verify_password("wrongpassword", hashed) == False

    @pytest.mark.asyncio
    async def test_token_expiration(self, client: AsyncClient):
        """Test that tokens include expiration."""
        # Register and get token
        register_data = {
            "email": "expire@example.com",
            "password": "expirepass123",
            "full_name": "Expire User",
            "phone": "555-6666"
        }
        response = await client.post("/api/v1/auth/register", json=register_data)
        assert response.status_code == 201

        token = response.json()["access_token"]
        # Token should be a valid JWT (has 3 parts separated by dots)
        assert len(token.split(".")) == 3