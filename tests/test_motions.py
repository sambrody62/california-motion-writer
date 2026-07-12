"""
Tests for motion management endpoints
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


class TestMotions:
    """Test motion CRUD operations."""

    @pytest.mark.asyncio
    async def test_create_motion(self, client: AsyncClient, auth_headers: dict, sample_motion_data):
        """Test creating a new motion."""
        response = await client.post(
            "/api/v1/motions",
            json=sample_motion_data,
            headers=auth_headers
        )

        assert response.status_code == 201
        data = response.json()

        assert data["motion_type"] == sample_motion_data["motion_type"]
        assert data["title"] == sample_motion_data["title"]
        assert data["status"] == "draft"  # Default status
        assert "id" in data
        assert "created_at" in data

    @pytest.mark.asyncio
    async def test_create_motion_invalid_type(self, client: AsyncClient, auth_headers: dict):
        """Test creating motion with invalid type."""
        invalid_data = {
            "motion_type": "INVALID",
            "title": "Invalid Motion",
            "description": "This should fail"
        }

        response = await client.post(
            "/api/v1/motions",
            json=invalid_data,
            headers=auth_headers
        )

        assert response.status_code in [400, 422]

    @pytest.mark.asyncio
    async def test_create_motion_unauthenticated(self, client: AsyncClient, sample_motion_data):
        """Test creating motion without authentication."""
        response = await client.post("/api/v1/motions", json=sample_motion_data)
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_list_motions(self, client: AsyncClient, auth_headers: dict, sample_motion_data):
        """Test listing user's motions — returns bare array."""
        # Create a few motions
        for i in range(3):
            motion_data = sample_motion_data.copy()
            motion_data["title"] = f"Motion {i+1}"
            await client.post("/api/v1/motions", json=motion_data, headers=auth_headers)

        # List motions
        response = await client.get("/api/v1/motions", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 3

    @pytest.mark.asyncio
    async def test_get_motion_by_id(self, client: AsyncClient, auth_headers: dict, sample_motion_data):
        """Test getting a specific motion by ID."""
        # Create a motion
        create_response = await client.post(
            "/api/v1/motions",
            json=sample_motion_data,
            headers=auth_headers
        )
        motion_id = create_response.json()["id"]

        # Get the motion
        response = await client.get(f"/api/v1/motions/{motion_id}", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == motion_id
        assert data["title"] == sample_motion_data["title"]

    @pytest.mark.asyncio
    async def test_get_motion_not_found(self, client: AsyncClient, auth_headers: dict):
        """Test getting non-existent motion."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = await client.get(f"/api/v1/motions/{fake_id}", headers=auth_headers)
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_motion(self, client: AsyncClient, auth_headers: dict, sample_motion_data):
        """Test updating a motion."""
        # Create a motion
        create_response = await client.post(
            "/api/v1/motions",
            json=sample_motion_data,
            headers=auth_headers
        )
        motion_id = create_response.json()["id"]

        # Update the motion
        update_data = {
            "title": "Updated Motion Title",
            "description": "Updated description",
            "status": "in_progress"
        }
        response = await client.put(
            f"/api/v1/motions/{motion_id}",
            json=update_data,
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == update_data["title"]
        assert data["description"] == update_data["description"]
        assert data["status"] == update_data["status"]

    @pytest.mark.asyncio
    async def test_motion_status_transitions(self, client: AsyncClient, auth_headers: dict, sample_motion_data):
        """Test valid motion status transitions."""
        # Create a motion (starts as 'draft')
        create_response = await client.post(
            "/api/v1/motions",
            json=sample_motion_data,
            headers=auth_headers
        )
        motion_id = create_response.json()["id"]

        # Valid transitions: draft -> in_progress -> completed
        status_updates = ["in_progress", "completed"]

        for status in status_updates:
            response = await client.put(
                f"/api/v1/motions/{motion_id}",
                json={"status": status},
                headers=auth_headers
            )
            assert response.status_code == 200
            assert response.json()["status"] == status

    @pytest.mark.asyncio
    async def test_delete_motion(self, client: AsyncClient, auth_headers: dict, sample_motion_data):
        """Test deleting a motion."""
        # Create a motion
        create_response = await client.post(
            "/api/v1/motions",
            json=sample_motion_data,
            headers=auth_headers
        )
        motion_id = create_response.json()["id"]

        # Delete the motion
        response = await client.delete(f"/api/v1/motions/{motion_id}", headers=auth_headers)
        assert response.status_code == 204

        # Verify it's deleted
        get_response = await client.get(f"/api/v1/motions/{motion_id}", headers=auth_headers)
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    @pytest.mark.xfail(reason="profile autofill integration not yet implemented — M1", strict=False)
    async def test_motion_with_profile_autofill(self, client: AsyncClient, auth_headers: dict):
        """Test motion creation with profile data auto-fill."""
        # First create a profile
        profile_data = {
            "case_number": "FL-2024-TEST",
            "county": "Los Angeles",
            "court_branch": "Test Court",
            "department": "Dept. T",
            "is_petitioner": True,
            "party_name": "Test Party",
            "party_address": "123 Test St",
            "party_phone": "555-TEST",
            "other_party_name": "Other Party",
            "other_party_address": "456 Other St"
        }

        profile_response = await client.post(
            "/api/v1/profiles",
            json=profile_data,
            headers=auth_headers
        )

        # Create motion with profile reference
        motion_data = {
            "motion_type": "RFO",
            "title": "Motion with Profile",
            "description": "Testing profile integration",
            "use_profile": True  # Flag to use profile data
        }

        response = await client.post(
            "/api/v1/motions",
            json=motion_data,
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        # Check if profile data was used
        assert data.get("case_caption") is not None

    @pytest.mark.asyncio
    async def test_motion_draft_saving(self, client: AsyncClient, auth_headers: dict, sample_motion_data):
        """Test saving motion drafts."""
        # Create a motion
        create_response = await client.post(
            "/api/v1/motions",
            json=sample_motion_data,
            headers=auth_headers
        )
        motion_id = create_response.json()["id"]

        # Save a draft
        draft_data = {
            "step_number": 1,
            "step_name": "Basic Information",
            "question_data": {
                "reason": "Test reason",
                "urgency": "normal"
            }
        }

        response = await client.post(
            f"/api/v1/motions/{motion_id}/drafts",
            json=draft_data,
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["step_number"] == draft_data["step_number"]
        assert data["question_data"] == draft_data["question_data"]

    @pytest.mark.asyncio
    @pytest.mark.xfail(reason="LLM processing endpoint not yet implemented — M1", strict=False)
    async def test_motion_llm_processing(self, client: AsyncClient, auth_headers: dict, sample_motion_data):
        """Test motion processing with LLM."""
        # Create a motion with intake data
        motion_data = sample_motion_data.copy()
        motion_data["intake_data"] = {
            "reason": "I need to modify custody arrangements",
            "children_involved": True,
            "urgency": "emergency"
        }

        create_response = await client.post(
            "/api/v1/motions",
            json=motion_data,
            headers=auth_headers
        )
        motion_id = create_response.json()["id"]

        # Process with LLM
        response = await client.post(
            f"/api/v1/motions/{motion_id}/process",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "generated_text" in data
        # Since we're using mock LLM, check for mock response
        assert len(data["generated_text"]) > 0
