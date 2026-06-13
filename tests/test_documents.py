"""
Tests for document endpoints — Bug 4 (download) and Bug 2 (profile model columns).
"""
import pytest
import uuid
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User, Profile
from app.models.motion import Motion, MotionType, MotionDraft, Document


# ---------------------------------------------------------------------------
# Bug 2: Profile model has new columns
# ---------------------------------------------------------------------------

class TestProfileModelNewColumns:
    """Profile ORM model must expose city, zip_code, and state columns."""

    @pytest.mark.asyncio
    async def test_profile_has_city_column(self, test_db: AsyncSession):
        """Profile model has a 'city' nullable string column."""
        user = User(
            email="city-test@example.com",
            password_hash="hashed",
            full_name="City Test"
        )
        test_db.add(user)
        await test_db.commit()
        await test_db.refresh(user)

        profile = Profile(user_id=user.id, city="Los Angeles")
        test_db.add(profile)
        await test_db.commit()
        await test_db.refresh(profile)

        assert profile.city == "Los Angeles"

    @pytest.mark.asyncio
    async def test_profile_has_zip_code_column(self, test_db: AsyncSession):
        """Profile model has a 'zip_code' nullable string column."""
        user = User(
            email="zip-test@example.com",
            password_hash="hashed",
            full_name="Zip Test"
        )
        test_db.add(user)
        await test_db.commit()
        await test_db.refresh(user)

        profile = Profile(user_id=user.id, zip_code="90001")
        test_db.add(profile)
        await test_db.commit()
        await test_db.refresh(profile)

        assert profile.zip_code == "90001"

    @pytest.mark.asyncio
    async def test_profile_state_defaults_to_ca(self, test_db: AsyncSession):
        """Profile model 'state' column defaults to 'CA' when not provided."""
        user = User(
            email="state-test@example.com",
            password_hash="hashed",
            full_name="State Test"
        )
        test_db.add(user)
        await test_db.commit()
        await test_db.refresh(user)

        profile = Profile(user_id=user.id)
        test_db.add(profile)
        await test_db.commit()
        await test_db.refresh(profile)

        assert profile.state == "CA"

    @pytest.mark.asyncio
    async def test_profile_city_zip_state_nullable(self, test_db: AsyncSession):
        """Profile can be created without city, zip_code, or state."""
        user = User(
            email="nullable-test@example.com",
            password_hash="hashed",
            full_name="Nullable Test"
        )
        test_db.add(user)
        await test_db.commit()
        await test_db.refresh(user)

        profile = Profile(user_id=user.id, city=None, zip_code=None, state=None)
        test_db.add(profile)
        await test_db.commit()
        await test_db.refresh(profile)

        assert profile.city is None
        assert profile.zip_code is None

    @pytest.mark.asyncio
    async def test_profile_all_new_columns_persist(self, test_db: AsyncSession):
        """All three new columns persist and are retrievable."""
        user = User(
            email="all-cols@example.com",
            password_hash="hashed",
            full_name="All Cols"
        )
        test_db.add(user)
        await test_db.commit()
        await test_db.refresh(user)

        profile = Profile(
            user_id=user.id,
            city="San Francisco",
            zip_code="94102",
            state="CA"
        )
        test_db.add(profile)
        await test_db.commit()

        result = await test_db.execute(
            select(Profile).where(Profile.user_id == user.id)
        )
        fetched = result.scalar_one()
        assert fetched.city == "San Francisco"
        assert fetched.zip_code == "94102"
        assert fetched.state == "CA"


# ---------------------------------------------------------------------------
# Bug 4: GET /{document_id}/download returns PDF bytes
# ---------------------------------------------------------------------------

async def _create_user_and_motion(db: AsyncSession):
    """Helper: create user, profile, motion, draft, and document records."""
    user = User(
        email=f"dl-{uuid.uuid4()}@example.com",
        password_hash="hashed",
        full_name="Download Test",
        is_active=True,
        email_verified=True
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    profile = Profile(
        user_id=user.id,
        party_name="John Download",
        other_party_name="Jane Download",
        county="Los Angeles",
        case_number="FL-2024-DL",
        is_petitioner=True
    )
    db.add(profile)
    await db.commit()
    await db.refresh(profile)

    motion = Motion(
        user_id=user.id,
        profile_id=profile.id,
        motion_type=MotionType.RFO,
        status="completed",
        case_caption="Download v. Download",
        title="Test RFO"
    )
    db.add(motion)
    await db.commit()
    await db.refresh(motion)

    draft = MotionDraft(
        motion_id=motion.id,
        step_number=1,
        step_name="relief_requested",
        question_data={"relief": "custody"},
        llm_output="Petitioner requests an order modifying custody."
    )
    db.add(draft)

    document = Document(
        motion_id=motion.id,
        document_type="FL-300",
        filename="test_FL-300_20240101.pdf",
        gcs_url="",
        generation_method="automated"
    )
    db.add(document)
    await db.commit()
    await db.refresh(document)

    return user, motion, document


class TestDocumentDownload:
    """Test GET /{document_id}/download endpoint (Bug 4)."""

    @pytest.mark.asyncio
    async def test_download_returns_pdf_bytes(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Download endpoint returns 200 with application/pdf when PDF service succeeds."""
        fake_pdf = b"%PDF-1.4 fake pdf content for testing"

        # Create motion
        motion_resp = await client.post(
            "/api/v1/motions",
            json={
                "motion_type": "RFO",
                "title": "Test RFO Download",
                "description": "Custody modification",
                "case_caption": "Smith v. Smith",
                "filing_track": "standard",
                "courthouse": "LA Superior",
                "intake_data": {}
            },
            headers=auth_headers
        )
        assert motion_resp.status_code == 201, motion_resp.text
        motion_id = motion_resp.json()["id"]

        # Create profile (may already exist if fixture ran — treat 400 as ok)
        await client.post(
            "/api/v1/profiles",
            json={
                "case_number": "FL-2024-DL",
                "county": "Los Angeles",
                "party_name": "Download User",
                "other_party_name": "Other Party",
                "is_petitioner": True
            },
            headers=auth_headers
        )

        # Save a draft so generate-pdf-sync doesn't 400
        draft_resp = await client.post(
            f"/api/v1/motions/{motion_id}/drafts",
            json={
                "step_number": 1,
                "step_name": "relief_requested",
                "question_data": {"relief": "custody modification"}
            },
            headers=auth_headers
        )
        assert draft_resp.status_code in (200, 201), draft_resp.text

        # Generate document record via sync endpoint (PDF service mocked)
        with patch(
            "app.api.v1.endpoints.documents.pdf_service.generate_motion_pdf",
            new=AsyncMock(return_value=fake_pdf)
        ):
            sync_resp = await client.post(
                "/api/v1/documents/generate-pdf-sync",
                json={"motion_id": motion_id},
                headers=auth_headers
            )
            assert sync_resp.status_code == 200, sync_resp.text

        # Retrieve the document_id from the list endpoint
        list_resp = await client.get(
            f"/api/v1/documents/motion/{motion_id}/documents",
            headers=auth_headers
        )
        assert list_resp.status_code == 200
        docs = list_resp.json()["documents"]
        assert len(docs) > 0
        document_id = docs[0]["id"]

        # Test the download endpoint
        with patch(
            "app.api.v1.endpoints.documents.pdf_service.generate_motion_pdf",
            new=AsyncMock(return_value=fake_pdf)
        ):
            dl_resp = await client.get(
                f"/api/v1/documents/{document_id}/download",
                headers=auth_headers
            )

        assert dl_resp.status_code == 200
        assert dl_resp.headers["content-type"] == "application/pdf"
        assert dl_resp.content == fake_pdf

    @pytest.mark.asyncio
    async def test_download_not_found_returns_404(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Download endpoint returns 404 for unknown document_id."""
        fake_id = str(uuid.uuid4())
        response = await client.get(
            f"/api/v1/documents/{fake_id}/download",
            headers=auth_headers
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_download_requires_auth(self, client: AsyncClient):
        """Download endpoint returns 401 without auth token."""
        fake_id = str(uuid.uuid4())
        response = await client.get(f"/api/v1/documents/{fake_id}/download")
        assert response.status_code == 401


# ---------------------------------------------------------------------------
# generate-pdf-sync uses generate_packet (multi-form packet support)
# ---------------------------------------------------------------------------

class TestGeneratePdfSyncUsesPacket:
    """generate-pdf-sync must delegate to generate_packet, not single-form generation."""

    @pytest.mark.asyncio
    async def test_sync_endpoint_calls_generate_packet(
        self, client: AsyncClient, auth_headers: dict
    ):
        """generate-pdf-sync calls generate_packet and returns PDF bytes."""
        fake_pdf = b"%PDF-1.4 packet pdf for testing"

        motion_resp = await client.post(
            "/api/v1/motions",
            json={
                "motion_type": "RFO",
                "title": "Packet Test RFO",
                "description": "Custody modification",
                "case_caption": "Packet v. Packet",
                "filing_track": "standard",
                "courthouse": "SD Superior",
                "intake_data": {}
            },
            headers=auth_headers
        )
        assert motion_resp.status_code == 201, motion_resp.text
        motion_id = motion_resp.json()["id"]

        await client.post(
            "/api/v1/profiles",
            json={
                "case_number": "FL-2024-PKT",
                "county": "San Diego",
                "party_name": "Packet User",
                "other_party_name": "Other Packet",
                "is_petitioner": True
            },
            headers=auth_headers
        )

        draft_resp = await client.post(
            f"/api/v1/motions/{motion_id}/drafts",
            json={
                "step_number": 1,
                "step_name": "relief_requested",
                "question_data": {"relief": "custody modification"}
            },
            headers=auth_headers
        )
        assert draft_resp.status_code in (200, 201), draft_resp.text

        with patch(
            "app.api.v1.endpoints.documents.generate_packet",
            new=AsyncMock(return_value=fake_pdf)
        ):
            resp = await client.post(
                "/api/v1/documents/generate-pdf-sync",
                json={"motion_id": motion_id},
                headers=auth_headers
            )

        assert resp.status_code == 200, resp.text
        assert resp.headers["content-type"] == "application/pdf"
        assert resp.content == fake_pdf

    @pytest.mark.asyncio
    async def test_sync_endpoint_support_issue_passes_motion_to_packet(
        self, client: AsyncClient, auth_headers: dict
    ):
        """generate-pdf-sync passes the motion ORM object to generate_packet."""
        fake_pdf = b"%PDF-1.4 support packet"
        captured: dict = {}

        async def _mock_packet(motion, profile, llm_sections, evidence=None):
            captured["motion"] = motion
            captured["intake_data"] = getattr(motion, "intake_data", {})
            return fake_pdf

        motion_resp = await client.post(
            "/api/v1/motions",
            json={
                "motion_type": "RFO",
                "title": "Support Packet Test",
                "description": "Support issue",
                "case_caption": "Support v. Support",
                "filing_track": "standard",
                "courthouse": "SD Superior",
                "intake_data": {"has_support_issue": True}
            },
            headers=auth_headers
        )
        assert motion_resp.status_code == 201, motion_resp.text
        motion_id = motion_resp.json()["id"]

        await client.post(
            "/api/v1/profiles",
            json={
                "case_number": "FL-2024-SUP",
                "county": "San Diego",
                "party_name": "Support User",
                "other_party_name": "Other Support",
                "is_petitioner": True
            },
            headers=auth_headers
        )

        await client.post(
            f"/api/v1/motions/{motion_id}/drafts",
            json={
                "step_number": 1,
                "step_name": "support_facts",
                "question_data": {"relief": "child support"}
            },
            headers=auth_headers
        )

        with patch(
            "app.api.v1.endpoints.documents.generate_packet",
            new=_mock_packet
        ):
            resp = await client.post(
                "/api/v1/documents/generate-pdf-sync",
                json={"motion_id": motion_id},
                headers=auth_headers
            )

        assert resp.status_code == 200, resp.text
        assert "motion" in captured, "generate_packet must be called with motion ORM object"
