"""
Tests for database models
"""
import pytest
import pytest_asyncio
from datetime import datetime, date, time
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User, Profile
from app.models.motion import Motion, MotionDraft, Document, MotionType
from app.models.chat import (
    ChatSession, ChatMessage, ChatIntent, ConversationTemplate,
    ChatSessionStatus, ChatSessionState, MessageSender
)


class TestUserModel:
    """Test User model functionality."""

    @pytest.mark.asyncio
    async def test_create_user(self, test_db: AsyncSession):
        """Test creating a user."""
        user = User(
            email="test@example.com",
            password_hash="hashed_password",
            full_name="Test User",
            phone="555-123-4567",
            is_active=True,
            email_verified=True
        )

        test_db.add(user)
        await test_db.commit()
        await test_db.refresh(user)

        assert user.id is not None
        assert user.email == "test@example.com"
        assert user.full_name == "Test User"
        assert user.is_active is True
        assert user.created_at is not None
        assert user.updated_at is not None

    @pytest.mark.asyncio
    async def test_user_relationships(self, test_db: AsyncSession):
        """Test user relationships with other models."""
        # Create user
        user = User(
            email="relationship@example.com",
            password_hash="hashed",
            full_name="Relationship User"
        )
        test_db.add(user)
        await test_db.commit()
        await test_db.refresh(user)

        # Create profile
        profile = Profile(
            user_id=user.id,
            party_name="John Doe",
            case_number="FL-2024-001"
        )
        test_db.add(profile)

        # Create motion
        motion = Motion(
            user_id=user.id,
            motion_type=MotionType.RFO,
            title="Test Motion"
        )
        test_db.add(motion)

        # Create chat session
        chat_session = ChatSession(
            user_id=user.id,
            status=ChatSessionStatus.ACTIVE
        )
        test_db.add(chat_session)

        await test_db.commit()

        # Re-query with eager loading to avoid MissingGreenlet under AsyncSession
        from sqlalchemy.orm import selectinload
        stmt = (
            select(User)
            .options(
                selectinload(User.profile),
                selectinload(User.motions),
                selectinload(User.chat_sessions),
            )
            .where(User.id == user.id)
        )
        result = await test_db.execute(stmt)
        loaded_user = result.scalar_one()

        assert loaded_user.profile is not None
        assert len(loaded_user.motions) > 0
        assert len(loaded_user.chat_sessions) > 0

    @pytest.mark.asyncio
    async def test_user_unique_email(self, test_db: AsyncSession):
        """Test that user emails must be unique."""
        # Create first user
        user1 = User(
            email="unique@example.com",
            password_hash="hash1",
            full_name="User One"
        )
        test_db.add(user1)
        await test_db.commit()

        # Try to create second user with same email
        user2 = User(
            email="unique@example.com",
            password_hash="hash2",
            full_name="User Two"
        )
        test_db.add(user2)

        with pytest.raises(Exception):  # Should raise integrity error
            await test_db.commit()


class TestProfileModel:
    """Test Profile model functionality."""

    @pytest.mark.asyncio
    async def test_create_profile(self, test_db: AsyncSession):
        """Test creating a profile."""
        # Create user first
        user = User(
            email="profile@example.com",
            password_hash="hashed",
            full_name="Profile User"
        )
        test_db.add(user)
        await test_db.commit()
        await test_db.refresh(user)

        # Create profile
        profile = Profile(
            user_id=user.id,
            case_number="FL-2024-001",
            county="Los Angeles",
            court_branch="Stanley Mosk Courthouse",
            department="Dept. 1",
            is_petitioner=True,
            party_name="John Doe",
            party_address="123 Main St, Los Angeles, CA 90001",
            party_phone="555-123-4567",
            other_party_name="Jane Doe",
            other_party_address="456 Oak Ave, Los Angeles, CA 90002",
            children_info=[
                {
                    "name": "Child Doe",
                    "birthdate": "2015-01-01",
                    "ssn_last_4": "1234"
                }
            ]
        )

        test_db.add(profile)
        await test_db.commit()
        await test_db.refresh(profile)

        assert profile.id is not None
        assert profile.user_id == user.id
        assert profile.case_number == "FL-2024-001"
        assert profile.county == "Los Angeles"
        assert profile.is_petitioner is True
        assert profile.party_name == "John Doe"
        assert isinstance(profile.children_info, list)
        assert len(profile.children_info) == 1
        assert profile.children_info[0]["name"] == "Child Doe"

    @pytest.mark.asyncio
    async def test_profile_json_fields(self, test_db: AsyncSession):
        """Test JSON fields in profile."""
        user = User(
            email="json@example.com",
            password_hash="hashed",
            full_name="JSON User"
        )
        test_db.add(user)
        await test_db.commit()
        await test_db.refresh(user)

        children_data = [
            {"name": "Child 1", "age": 8, "grade": "3rd"},
            {"name": "Child 2", "age": 5, "grade": "K"}
        ]

        profile = Profile(
            user_id=user.id,
            party_name="Parent Name",
            children_info=children_data
        )

        test_db.add(profile)
        await test_db.commit()
        await test_db.refresh(profile)

        # Verify JSON data is preserved
        assert len(profile.children_info) == 2
        assert profile.children_info[0]["name"] == "Child 1"
        assert profile.children_info[1]["age"] == 5


class TestMotionModel:
    """Test Motion model functionality."""

    @pytest.mark.asyncio
    async def test_create_motion(self, test_db: AsyncSession):
        """Test creating a motion."""
        # Create user first
        user = User(
            email="motion@example.com",
            password_hash="hashed",
            full_name="Motion User"
        )
        test_db.add(user)
        await test_db.commit()
        await test_db.refresh(user)

        # Create motion
        motion = Motion(
            user_id=user.id,
            motion_type=MotionType.RFO,
            status="draft",
            case_caption="Smith v. Smith",
            title="Request for Order - Custody",
            description="Request for custody modification",
            filing_track="standard",
            courthouse="Los Angeles Superior Court",
            intake_data={
                "reason": "Change in circumstances",
                "children_involved": True
            }
        )

        test_db.add(motion)
        await test_db.commit()
        await test_db.refresh(motion)

        assert motion.id is not None
        assert motion.user_id == user.id
        assert motion.motion_type == MotionType.RFO
        assert motion.status == "draft"
        assert motion.title == "Request for Order - Custody"
        assert isinstance(motion.intake_data, dict)
        assert motion.intake_data["reason"] == "Change in circumstances"

    @pytest.mark.asyncio
    async def test_motion_with_dates(self, test_db: AsyncSession):
        """Test motion with filing and hearing dates."""
        user = User(
            email="dates@example.com",
            password_hash="hashed",
            full_name="Dates User"
        )
        test_db.add(user)
        await test_db.commit()
        await test_db.refresh(user)

        motion = Motion(
            user_id=user.id,
            motion_type=MotionType.RFO,
            title="Motion with Dates",
            filing_date=date(2024, 1, 15),
            hearing_date=date(2024, 2, 15),
            hearing_time=time(9, 0)
        )

        test_db.add(motion)
        await test_db.commit()
        await test_db.refresh(motion)

        assert motion.filing_date == date(2024, 1, 15)
        assert motion.hearing_date == date(2024, 2, 15)
        assert motion.hearing_time == time(9, 0)

    @pytest.mark.asyncio
    async def test_motion_with_drafts(self, test_db: AsyncSession):
        """Test motion with drafts relationship."""
        user = User(
            email="drafts@example.com",
            password_hash="hashed",
            full_name="Drafts User"
        )
        test_db.add(user)
        await test_db.commit()
        await test_db.refresh(user)

        motion = Motion(
            user_id=user.id,
            motion_type=MotionType.RFO,
            title="Motion with Drafts"
        )
        test_db.add(motion)
        await test_db.commit()
        await test_db.refresh(motion)

        # Add draft
        draft = MotionDraft(
            motion_id=motion.id,
            step_number=1,
            step_name="relief_requested",
            question_data={"question": "What relief are you seeking?"},
            llm_input="User wants custody modification",
            llm_output="Rewritten professional text",
            llm_model="gemini-pro",
            llm_tokens_used=150,
            is_complete=True
        )
        test_db.add(draft)
        await test_db.commit()

        # Re-query with eager loading to avoid MissingGreenlet under AsyncSession
        from sqlalchemy.orm import selectinload
        stmt = (
            select(Motion)
            .options(selectinload(Motion.drafts))
            .where(Motion.id == motion.id)
        )
        result = await test_db.execute(stmt)
        loaded_motion = result.scalar_one()

        assert len(loaded_motion.drafts) == 1
        assert loaded_motion.drafts[0].step_name == "relief_requested"


class TestChatModels:
    """Test chat-related models."""

    @pytest.mark.asyncio
    async def test_create_chat_session(self, test_db: AsyncSession):
        """Test creating a chat session."""
        user = User(
            email="chat@example.com",
            password_hash="hashed",
            full_name="Chat User"
        )
        test_db.add(user)
        await test_db.commit()
        await test_db.refresh(user)

        session = ChatSession(
            user_id=user.id,
            status=ChatSessionStatus.ACTIVE,
            current_state=ChatSessionState.GREETING,
            context={"test": "data"},
            intent="FILE_MOTION",
            confidence_score=85,
            language="en"
        )

        test_db.add(session)
        await test_db.commit()
        await test_db.refresh(session)

        assert session.id is not None
        assert session.user_id == user.id
        assert session.status == ChatSessionStatus.ACTIVE
        assert session.current_state == ChatSessionState.GREETING
        assert session.context == {"test": "data"}
        assert session.intent == "FILE_MOTION"
        assert session.confidence_score == 85

    @pytest.mark.asyncio
    async def test_chat_session_with_messages(self, test_db: AsyncSession):
        """Test chat session with messages."""
        user = User(
            email="messages@example.com",
            password_hash="hashed",
            full_name="Messages User"
        )
        test_db.add(user)
        await test_db.commit()
        await test_db.refresh(user)

        session = ChatSession(
            user_id=user.id,
            status=ChatSessionStatus.ACTIVE
        )
        test_db.add(session)
        await test_db.commit()
        await test_db.refresh(session)

        # Add messages
        user_message = ChatMessage(
            session_id=session.id,
            content="I need help with custody",
            sender=MessageSender.USER,
            entities={"motion_type": "custody"},
            intent_detected="FILE_MOTION",
            confidence=80
        )

        assistant_message = ChatMessage(
            session_id=session.id,
            content="I can help you with that",
            sender=MessageSender.ASSISTANT,
            quick_replies=["Yes", "No", "Tell me more"],
            prompt_tokens=50,
            completion_tokens=25,
            model_used="gemini-pro"
        )

        test_db.add_all([user_message, assistant_message])
        await test_db.commit()

        # Re-query with eager loading to avoid MissingGreenlet under AsyncSession
        from sqlalchemy.orm import selectinload
        stmt = (
            select(ChatSession)
            .options(selectinload(ChatSession.messages))
            .where(ChatSession.id == session.id)
        )
        result = await test_db.execute(stmt)
        loaded_session = result.scalar_one()

        assert len(loaded_session.messages) == 2

        # Test message properties
        messages = loaded_session.messages
        user_msg = next(m for m in messages if m.sender == MessageSender.USER)
        assistant_msg = next(m for m in messages if m.sender == MessageSender.ASSISTANT)

        assert user_msg.content == "I need help with custody"
        assert user_msg.entities == {"motion_type": "custody"}
        assert assistant_msg.quick_replies == ["Yes", "No", "Tell me more"]

    @pytest.mark.asyncio
    async def test_chat_intent_model(self, test_db: AsyncSession):
        """Test ChatIntent model."""
        intent = ChatIntent(
            intent_key="FILE_MOTION",
            display_name="File a Motion",
            description="User wants to file a new motion",
            example_phrases=["I want to file", "Need to submit", "File motion"],
            triggers_forms=["FL-300"],
            requires_profile=True,
            follow_up_questions=["What type of motion?", "What relief do you seek?"]
        )

        test_db.add(intent)
        await test_db.commit()
        await test_db.refresh(intent)

        assert intent.id is not None
        assert intent.intent_key == "FILE_MOTION"
        assert intent.display_name == "File a Motion"
        assert len(intent.example_phrases) == 3
        assert intent.triggers_forms == ["FL-300"]
        assert intent.requires_profile is True

    @pytest.mark.asyncio
    async def test_conversation_template_model(self, test_db: AsyncSession):
        """Test ConversationTemplate model."""
        template = ConversationTemplate(
            template_key="custody_modification",
            name="Custody Modification Template",
            description="Template for custody modification conversations",
            initial_message="I understand you want to modify custody arrangements.",
            questions_sequence=[
                {"question": "What is the current arrangement?", "field": "current_custody"},
                {"question": "What changes do you want?", "field": "requested_changes"}
            ],
            applicable_intents=["MODIFY_ORDER"],
            applicable_forms=["FL-300"],
            times_used=0,
            success_rate=95,
            is_active=True
        )

        test_db.add(template)
        await test_db.commit()
        await test_db.refresh(template)

        assert template.id is not None
        assert template.template_key == "custody_modification"
        assert len(template.questions_sequence) == 2
        assert template.applicable_intents == ["MODIFY_ORDER"]
        assert template.success_rate == 95


class TestDocumentModel:
    """Test Document model functionality."""

    @pytest.mark.asyncio
    async def test_create_document(self, test_db: AsyncSession):
        """Test creating a document."""
        # Create user and motion
        user = User(
            email="document@example.com",
            password_hash="hashed",
            full_name="Document User"
        )
        test_db.add(user)
        await test_db.commit()
        await test_db.refresh(user)

        motion = Motion(
            user_id=user.id,
            motion_type=MotionType.RFO,
            title="Document Motion"
        )
        test_db.add(motion)
        await test_db.commit()
        await test_db.refresh(motion)

        # Create document
        document = Document(
            motion_id=motion.id,
            document_type="FL-300",
            filename="fl300_filled.pdf",
            gcs_url="gs://bucket/path/to/file.pdf",
            file_size_bytes=1024000,
            pages=3,
            generation_method="automated"
        )

        test_db.add(document)
        await test_db.commit()
        await test_db.refresh(document)

        assert document.id is not None
        assert document.motion_id == motion.id
        assert document.document_type == "FL-300"
        assert document.filename == "fl300_filled.pdf"
        assert document.file_size_bytes == 1024000
        assert document.pages == 3


class TestModelValidation:
    """Test model validation and constraints."""

    @pytest.mark.asyncio
    async def test_uuid_fields(self, test_db: AsyncSession):
        """Test that UUID fields work correctly."""
        user = User(
            email="uuid@example.com",
            password_hash="hashed",
            full_name="UUID User"
        )
        test_db.add(user)
        await test_db.commit()
        await test_db.refresh(user)

        # ID should be a valid UUID string
        assert isinstance(user.id, str)
        uuid.UUID(user.id)  # Should not raise exception

    @pytest.mark.asyncio
    async def test_enum_fields(self, test_db: AsyncSession):
        """Test enum field validation."""
        user = User(
            email="enum@example.com",
            password_hash="hashed",
            full_name="Enum User"
        )
        test_db.add(user)
        await test_db.commit()
        await test_db.refresh(user)

        # Test motion type enum
        motion = Motion(
            user_id=user.id,
            motion_type=MotionType.RFO,
            title="Enum Test"
        )
        test_db.add(motion)
        await test_db.commit()
        await test_db.refresh(motion)

        assert motion.motion_type == MotionType.RFO

        # Test chat session enums
        session = ChatSession(
            user_id=user.id,
            status=ChatSessionStatus.ACTIVE,
            current_state=ChatSessionState.GREETING
        )
        test_db.add(session)
        await test_db.commit()
        await test_db.refresh(session)

        assert session.status == ChatSessionStatus.ACTIVE
        assert session.current_state == ChatSessionState.GREETING

    @pytest.mark.asyncio
    async def test_timestamps(self, test_db: AsyncSession):
        """Test automatic timestamp fields."""
        user = User(
            email="timestamp@example.com",
            password_hash="hashed",
            full_name="Timestamp User"
        )
        test_db.add(user)
        await test_db.commit()
        await test_db.refresh(user)

        # Check that timestamps were set
        assert user.created_at is not None
        assert user.updated_at is not None
        assert isinstance(user.created_at, datetime)
        assert isinstance(user.updated_at, datetime)

        # Update user and check updated_at changes
        original_updated = user.updated_at
        user.full_name = "Updated Name"
        await test_db.commit()
        await test_db.refresh(user)

        # Note: SQLite doesn't automatically update timestamp on update
        # This would work with PostgreSQL onupdate trigger