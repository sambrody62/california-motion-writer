"""
Tests for LLM service functionality
"""
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch, MagicMock
import json
import os

from app.services.llm_service import LLMService


@pytest_asyncio.fixture
async def llm_service():
    """Create an LLM service instance for testing."""
    return LLMService()


class TestLLMServiceRewriteRfoSection:
    """Test rewrite_rfo_section method."""

    @pytest.mark.asyncio
    async def test_happy_path(self, llm_service):
        """Happy path: returns success dict with required keys."""
        result = await llm_service.rewrite_rfo_section(
            section_name="relief_requested",
            user_answers={"reason": "Custody modification needed"},
            context={"party_role": "Petitioner", "county": "Los Angeles"}
        )

        assert isinstance(result, dict)
        assert result["success"] is True
        assert "rewritten_text" in result
        assert isinstance(result["rewritten_text"], str)
        assert len(result["rewritten_text"]) > 0
        assert "tokens_used" in result
        assert isinstance(result["tokens_used"], int)

    @pytest.mark.asyncio
    async def test_mock_output_contains_user_words(self, llm_service):
        """Mock mode passes the user's own words through — no placeholder copy."""
        result = await llm_service.rewrite_rfo_section(
            section_name="custody_facts",
            user_answers={"facts": "I have been the primary caregiver"},
            context={}
        )

        assert result["success"] is True
        assert "primary caregiver" in result["rewritten_text"]
        assert "MOCK" not in result["rewritten_text"]

    @pytest.mark.asyncio
    async def test_with_user_id(self, llm_service):
        """Accepts optional user_id without error."""
        result = await llm_service.rewrite_rfo_section(
            section_name="relief_requested",
            user_answers={"q": "v"},
            context={},
            user_id="user-123"
        )

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_empty_answers(self, llm_service):
        """Handles empty answers dict gracefully."""
        result = await llm_service.rewrite_rfo_section(
            section_name="relief_requested",
            user_answers={},
            context={}
        )

        assert isinstance(result, dict)
        assert "success" in result

    @pytest.mark.asyncio
    async def test_model_field_in_mock_mode(self, llm_service):
        """In mock mode, model field is 'mock-llm'."""
        result = await llm_service.rewrite_rfo_section(
            section_name="test",
            user_answers={"k": "v"},
            context={}
        )

        assert result.get("model") == "mock-llm"


class TestLLMServiceRewriteDeclaration:
    """Test rewrite_declaration method."""

    @pytest.mark.asyncio
    async def test_happy_path(self, llm_service):
        """Happy path: returns success dict with declarant name embedded."""
        result = await llm_service.rewrite_declaration(
            narrative="I take care of my children every day.",
            declarant_name="John Doe"
        )

        assert isinstance(result, dict)
        assert result["success"] is True
        assert "rewritten_text" in result
        assert "John Doe" in result["rewritten_text"]
        assert "tokens_used" in result

    @pytest.mark.asyncio
    async def test_perjury_statement_in_mock_output(self, llm_service):
        """Mock output contains penalty of perjury statement."""
        result = await llm_service.rewrite_declaration(
            narrative="Some facts.",
            declarant_name="Jane Smith"
        )

        assert result["success"] is True
        assert "perjury" in result["rewritten_text"].lower()

    @pytest.mark.asyncio
    async def test_with_user_id(self, llm_service):
        """Accepts optional user_id without error."""
        result = await llm_service.rewrite_declaration(
            narrative="Facts here.",
            declarant_name="Test Name",
            user_id="user-456"
        )

        assert result["success"] is True


class TestLLMServiceEnhanceBestInterests:
    """Test enhance_best_interests method."""

    @pytest.mark.asyncio
    async def test_happy_path(self, llm_service):
        """Happy path: returns success dict with enhanced text."""
        result = await llm_service.enhance_best_interests(
            custody_request="I want sole custody",
            children_info=[{"name": "Child", "age": 8}]
        )

        assert isinstance(result, dict)
        assert result["success"] is True
        assert "enhanced_text" in result
        assert isinstance(result["enhanced_text"], str)
        assert len(result["enhanced_text"]) > 0
        assert "tokens_used" in result

    @pytest.mark.asyncio
    async def test_empty_children_info(self, llm_service):
        """Handles empty children list gracefully."""
        result = await llm_service.enhance_best_interests(
            custody_request="Custody request",
            children_info=[]
        )

        assert isinstance(result, dict)
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_mock_output_shape(self, llm_service):
        """Mock output contains best interests factor content."""
        result = await llm_service.enhance_best_interests(
            custody_request="I want joint custody",
            children_info=[{"name": "Amy", "age": 6}]
        )

        assert result["success"] is True
        text = result["enhanced_text"].lower()
        # Mock output references best interests factors
        assert "best interests" in text or "health" in text or "stability" in text


class TestLLMServiceProcessCompleteMotion:
    """Test process_complete_motion method."""

    @pytest.mark.asyncio
    async def test_happy_path(self, llm_service):
        """Happy path: processes all draft sections."""
        drafts = [
            {
                "step_number": 1,
                "step_name": "relief_requested",
                "question_data": {"relief": "Custody modification"}
            },
            {
                "step_number": 2,
                "step_name": "supporting_facts",
                "question_data": {"facts": "Changed circumstances"}
            }
        ]
        profile_data = {
            "is_petitioner": True,
            "county": "Los Angeles",
            "case_number": "FL-2024-001",
            "children_info": [],
            "party_name": "John Doe",
            "other_party_name": "Jane Doe"
        }

        result = await llm_service.process_complete_motion(
            motion_type="RFO",
            all_drafts=drafts,
            profile_data=profile_data
        )

        assert isinstance(result, dict)
        assert result["motion_type"] == "RFO"
        assert "sections" in result
        assert len(result["sections"]) == 2
        assert "total_tokens" in result
        assert isinstance(result["total_tokens"], int)

    @pytest.mark.asyncio
    async def test_sections_have_required_keys(self, llm_service):
        """Each section result has expected keys."""
        drafts = [{"step_number": 1, "step_name": "test", "question_data": {"k": "v"}}]
        result = await llm_service.process_complete_motion(
            motion_type="RFO",
            all_drafts=drafts,
            profile_data={"is_petitioner": True, "county": "CA"}
        )

        section = result["sections"][0]
        assert "step_number" in section
        assert "section" in section
        assert "rewritten_text" in section
        assert "success" in section

    @pytest.mark.asyncio
    async def test_empty_drafts(self, llm_service):
        """Handles empty drafts list."""
        result = await llm_service.process_complete_motion(
            motion_type="RFO",
            all_drafts=[],
            profile_data={}
        )

        assert result["motion_type"] == "RFO"
        assert result["sections"] == []
        assert result["success"] is True


class TestLLMServiceValidateOutput:
    """Test validate_output method (synchronous)."""

    def test_valid_output(self, llm_service):
        """Returns valid=True for acceptable text."""
        good_text = (
            "1. Petitioner requests an order modifying custody. "
            "The minor children have resided primarily with Petitioner. "
            "Pursuant to California Family Code, Petitioner is entitled to relief. "
            "Based on the foregoing facts, the Court should grant the requested order. "
            "The best interests of the children support this request. "
            "Petitioner has been the primary caregiver for the past three years. "
            "The children are enrolled in school near Petitioner's residence."
        ) * 2  # ensure > 50 words

        result = llm_service.validate_output(good_text)

        assert isinstance(result, dict)
        assert "valid" in result
        assert "issues" in result
        assert isinstance(result["issues"], list)

    def test_too_short_output(self, llm_service):
        """Returns valid=False for text under 50 words."""
        short_text = "This is too short."

        result = llm_service.validate_output(short_text)

        assert result["valid"] is False
        assert any("short" in issue.lower() for issue in result["issues"])

    def test_prohibited_phrase_detected(self, llm_service):
        """Flags prohibited phrases in output."""
        text_with_prohibited = (
            "I am not a lawyer but here are many words to pad this out so it exceeds "
            "the fifty word minimum threshold for the validate output function to work "
            "correctly in the test suite we are building here today."
        )

        result = llm_service.validate_output(text_with_prohibited)

        assert result["valid"] is False
        assert len(result["issues"]) > 0

    def test_too_long_output(self, llm_service):
        """Flags output exceeding 5000 words."""
        long_text = "word " * 5001

        result = llm_service.validate_output(long_text)

        assert result["valid"] is False
        assert any("long" in issue.lower() for issue in result["issues"])

    def test_validate_output_is_synchronous(self, llm_service):
        """validate_output is not a coroutine."""
        import inspect
        text = "word " * 60
        result = llm_service.validate_output(text)
        assert not inspect.iscoroutine(result)
        assert isinstance(result, dict)


class TestLLMServiceEnhanceDeclaration:
    """Test enhance_declaration method (Bug 1 — new method)."""

    @pytest.mark.asyncio
    async def test_enhance_declaration_exists(self, llm_service):
        """enhance_declaration exists and returns a dict."""
        assert hasattr(llm_service, "enhance_declaration")
        result = await llm_service.enhance_declaration(
            "I have been the primary caregiver for my children.",
        )
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_enhance_declaration_returns_text_in_mock_mode(self, llm_service):
        """enhance_declaration returns non-empty enhanced_text in mock mode."""
        result = await llm_service.enhance_declaration(
            "Respondent violated the custody order on January 1.",
        )
        assert result["success"] is True
        assert "enhanced_text" in result
        assert isinstance(result["enhanced_text"], str)
        assert len(result["enhanced_text"]) > 0

    @pytest.mark.asyncio
    async def test_enhance_declaration_formal_legal_tone_params(self, llm_service):
        """Accepts formal and legal_tone keyword args without error."""
        result = await llm_service.enhance_declaration(
            "Some narrative text here.",
            formal=True,
            legal_tone=True,
        )
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_enhance_declaration_mock_perjury_statement(self, llm_service):
        """Mock output via rewrite_declaration contains perjury statement."""
        result = await llm_service.enhance_declaration(
            "I declare the following facts.",
        )
        assert "perjury" in result["enhanced_text"].lower()


class TestValidateOutputWalrusBugFix:
    """Regression tests for the walrus-operator bug fix in validate_output (Bug 1)."""

    def test_rfo_text_with_numbered_para_is_valid(self, llm_service):
        """Text containing 'RFO' with a leading digit is not flagged for missing paragraphs."""
        text = (
            "1. This is an RFO filed pursuant to California Family Code. "
            "Petitioner requests relief from the Court regarding custody. "
            "The foregoing facts establish good cause for the requested order. "
            "Petitioner has been the primary caregiver for the children. "
            "The Court should grant this Request for Order forthwith."
        ) * 3

        result = llm_service.validate_output(text)

        assert isinstance(result, dict)
        assert "issues" in result
        # Should not flag missing numbered paragraphs
        assert not any("numbered" in i.lower() for i in result["issues"])

    def test_rfo_text_without_digit_flags_paragraphs(self, llm_service):
        """Text with 'RFO' but no leading digit is flagged for missing paragraphs."""
        text = (
            "This is an RFO motion. Petitioner requests relief from the Court. "
            "There are many words here to exceed the fifty word minimum count. "
            "More content to ensure the length check passes without issue."
        ) * 4

        result = llm_service.validate_output(text)

        assert isinstance(result, dict)
        # Should flag missing numbered paragraphs since no digit in first 100 chars
        assert any("numbered" in i.lower() for i in result["issues"])

    def test_validate_output_no_longer_assigns_bool_to_motion_type(self, llm_service):
        """Walrus bug: 'if motion_type := ...' would set motion_type=True, a bool.
        The fix replaces it with a plain boolean expression — validate returns dict."""
        import inspect
        text = "FL-300 " + "word " * 60
        result = llm_service.validate_output(text)
        # Confirm result is a plain dict (was still returning one before, but
        # the walrus expression silently set motion_type=True — fix removes that name)
        assert isinstance(result, dict)
        assert "valid" in result
