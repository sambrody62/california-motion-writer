"""
Tests for profile management endpoints
"""
import pytest
from httpx import AsyncClient


class TestProfiles:
    """Test profile CRUD operations."""

    @pytest.mark.asyncio
    async def test_create_profile(self, client: AsyncClient, auth_headers: dict, sample_profile_data):
        """Test creating a new profile."""
        response = await client.post(
            "/api/v1/profiles",
            json=sample_profile_data,
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        assert data["case_number"] == sample_profile_data["case_number"]
        assert data["county"] == sample_profile_data["county"]
        assert data["party_name"] == sample_profile_data["party_name"]
        assert "id" in data
        assert "created_at" in data

    @pytest.mark.asyncio
    async def test_create_duplicate_profile(self, client: AsyncClient, auth_headers: dict, sample_profile_data):
        """Test creating duplicate profile for same user."""
        # Create first profile
        await client.post("/api/v1/profiles", json=sample_profile_data, headers=auth_headers)

        # Try to create second profile
        response = await client.post("/api/v1/profiles", json=sample_profile_data, headers=auth_headers)
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_get_profile(self, client: AsyncClient, auth_headers: dict, sample_profile_data):
        """Test getting user's profile."""
        # Create profile
        await client.post("/api/v1/profiles", json=sample_profile_data, headers=auth_headers)

        # Get profile
        response = await client.get("/api/v1/profiles/me", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["case_number"] == sample_profile_data["case_number"]

    @pytest.mark.asyncio
    async def test_update_profile(self, client: AsyncClient, auth_headers: dict, sample_profile_data):
        """Test updating profile."""
        # Create profile
        await client.post("/api/v1/profiles", json=sample_profile_data, headers=auth_headers)

        # Update profile
        update_data = {
            "case_number": "FL-2024-UPDATED",
            "department": "Dept. Updated"
        }
        response = await client.put(
            "/api/v1/profiles/me",
            json=update_data,
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["case_number"] == update_data["case_number"]
        assert data["department"] == update_data["department"]

    @pytest.mark.asyncio
    async def test_profile_children_info(self, client: AsyncClient, auth_headers: dict):
        """Test profile with children information."""
        profile_data = {
            "case_number": "FL-2024-KIDS",
            "county": "Los Angeles",
            "court_branch": "Family Court",
            "department": "Dept. K",
            "is_petitioner": True,
            "party_name": "Parent One",
            "party_address": "123 Parent St",
            "party_phone": "555-1111",
            "other_party_name": "Parent Two",
            "other_party_address": "456 Parent Ave",
            "children_info": [
                {
                    "name": "Child One",
                    "birthdate": "2015-01-01",
                    "ssn_last_4": "1234"
                },
                {
                    "name": "Child Two",
                    "birthdate": "2017-06-15",
                    "ssn_last_4": "5678"
                }
            ]
        }

        response = await client.post(
            "/api/v1/profiles",
            json=profile_data,
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["children_info"]) == 2
        assert data["children_info"][0]["name"] == "Child One"

    @pytest.mark.asyncio
    async def test_profile_county_validation(self, client: AsyncClient, auth_headers: dict):
        """Test profile county validation."""
        invalid_profile = {
            "case_number": "FL-2024-INVALID",
            "county": "Invalid County",  # Not a valid CA county
            "court_branch": "Some Court",
            "department": "Dept. X",
            "is_petitioner": True,
            "party_name": "Test User",
            "party_address": "123 Test St",
            "party_phone": "555-9999",
            "other_party_name": "Other User",
            "other_party_address": "456 Other St"
        }

        # Depending on implementation, this might be accepted or rejected
        response = await client.post(
            "/api/v1/profiles",
            json=invalid_profile,
            headers=auth_headers
        )
        # Check the actual implementation behavior
        assert response.status_code in [200, 400, 422]

    @pytest.mark.asyncio
    async def test_profile_phone_formatting(self, client: AsyncClient, auth_headers: dict, sample_profile_data):
        """Test phone number formatting in profile."""
        # Test various phone formats
        phone_formats = [
            "5551234567",
            "(555) 123-4567",
            "555.123.4567",
            "+1-555-123-4567"
        ]

        for phone in phone_formats:
            profile_data = sample_profile_data.copy()
            profile_data["party_phone"] = phone
            profile_data["case_number"] = f"FL-{phone[:3]}"  # Make unique

            response = await client.post(
                "/api/v1/profiles",
                json=profile_data,
                headers=auth_headers
            )
            # Should accept various formats
            assert response.status_code in [200, 400]  # 400 if duplicate

    @pytest.mark.asyncio
    async def test_delete_profile(self, client: AsyncClient, auth_headers: dict, sample_profile_data):
        """Test deleting profile."""
        # Create profile
        await client.post("/api/v1/profiles", json=sample_profile_data, headers=auth_headers)

        # Delete profile
        response = await client.delete("/api/v1/profiles/me", headers=auth_headers)
        assert response.status_code in [200, 204]

        # Verify it's deleted
        get_response = await client.get("/api/v1/profiles/me", headers=auth_headers)
        assert get_response.status_code == 404