#!/usr/bin/env python3
"""
Simple test for chat to PDF workflow - tests the services directly
"""
import asyncio
import sys
import os
from datetime import datetime
import json

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock database setup
class MockDB:
    """Mock database for testing"""
    def __init__(self):
        self.data = {}

    async def execute(self, stmt):
        return self

    def scalar_one_or_none(self):
        return None

    async def commit(self):
        pass

    def add(self, obj):
        pass

async def test_llm_chat_service():
    """Test the LLM chat service"""
    print("\n=== Testing LLM Chat Service ===")

    try:
        from app.services.llm_chat_service import llm_chat_service

        # Test intent classification
        message = "I need to change our custody arrangement because my ex moved out of state"
        intent, entities, confidence = await llm_chat_service.classify_intent(
            message, []
        )

        print(f"✓ Intent Classification:")
        print(f"  Message: '{message[:50]}...'")
        print(f"  Intent: {intent}")
        print(f"  Confidence: {confidence:.2f}")
        print(f"  Entities: {entities}")

        # Test entity extraction
        entities = await llm_chat_service.extract_entities(
            "My name is Jane Smith and my ex is John Doe. We have two kids."
        )
        print(f"\n✓ Entity Extraction:")
        print(f"  Extracted: {entities}")

        return True
    except Exception as e:
        print(f"✗ LLM Chat Service failed: {e}")
        return False

async def test_question_graph():
    """Test the question graph service"""
    print("\n=== Testing Question Graph Service ===")

    try:
        from app.services.question_graph_service import QuestionGraph

        graph = QuestionGraph()

        # Test getting next question
        answered = {"motion_type": "custody"}
        profile_data = {"case_number": "123", "party_name": "Jane Smith"}

        next_q = graph.get_next_question("custody", answered, profile_data)

        if next_q:
            print(f"✓ Next Question:")
            print(f"  Field: {next_q['field_name']}")
            print(f"  Question: {next_q['question']}")
            print(f"  Type: {next_q['type']}")
        else:
            print("✓ No more questions needed")

        # Test multiple questions answered
        answered.update({
            "current_custody_arrangement": "joint",
            "requested_custody_arrangement": "sole"
        })

        next_q = graph.get_next_question("custody", answered, profile_data)
        if next_q:
            print(f"\n✓ Follow-up Question:")
            print(f"  Field: {next_q['field_name']}")
            print(f"  Question: {next_q['question']}")

        return True
    except Exception as e:
        print(f"✗ Question Graph failed: {e}")
        return False

async def test_form_mapper():
    """Test the form field mapper"""
    print("\n=== Testing Form Field Mapper ===")

    try:
        from app.services.form_field_mapper import form_mapper

        # Test data
        conversation_data = {
            "motion_type": "custody",
            "requested_custody_arrangement": "sole legal and physical custody",
            "change_reason": "Other parent relocated out of state",
            "is_emergency": False,
            "children_names": ["Alice Smith", "Bob Smith"]
        }

        profile_data = {
            "party_name": "Jane Smith",
            "other_party_name": "John Doe",
            "case_number": "FL-2024-001",
            "county": "San Diego"
        }

        # Map to FL-300
        mapped_fields = form_mapper.map_conversation_to_form(
            "FL-300", conversation_data, profile_data
        )

        print(f"✓ Field Mapping for FL-300:")
        for key, value in list(mapped_fields.items())[:5]:
            print(f"  {key}: {value}")

        # Validate fields
        is_valid, missing = form_mapper.validate_required_fields(
            "FL-300", mapped_fields
        )

        print(f"\n✓ Validation:")
        print(f"  Valid: {is_valid}")
        print(f"  Missing fields: {len(missing)}")
        if missing:
            for field in missing[:3]:
                print(f"    - {field}")

        return True
    except Exception as e:
        print(f"✗ Form Mapper failed: {e}")
        return False

async def test_memory_service():
    """Test the conversation memory service"""
    print("\n=== Testing Memory Service ===")

    try:
        from app.services.conversation_memory_service import MemoryService

        memory_service = MemoryService()

        # Test reference resolution
        text = "My ex hasn't paid support and I want to file against my ex"
        references = {
            "my ex": "John Doe",
            "support": "child support",
            "the kids": "Alice and Bob"
        }

        resolved = memory_service.resolve_references(text, references)
        print(f"✓ Reference Resolution:")
        print(f"  Original: '{text}'")
        print(f"  Resolved: '{resolved}'")

        # Test memory summarization
        messages = [
            {"content": "I need help with custody", "sender": "user"},
            {"content": "I can help with that", "sender": "assistant"},
            {"content": "My ex moved to Texas", "sender": "user"},
            {"content": "When did they move?", "sender": "assistant"},
            {"content": "Last month", "sender": "user"}
        ]

        summary = await memory_service.summarize_conversation(messages, max_length=100)
        print(f"\n✓ Conversation Summary:")
        print(f"  {summary}")

        return True
    except Exception as e:
        print(f"✗ Memory Service failed: {e}")
        return False

async def test_chat_to_pdf_integration():
    """Test the chat to PDF service integration"""
    print("\n=== Testing Chat to PDF Integration ===")

    try:
        # Create mock chat session
        class MockChatSession:
            def __init__(self):
                self.id = "test-session-123"
                self.intent = "MODIFY_ORDER"
                self.motion_type_detected = "custody_modification"
                self.context = {
                    "motion_type": "custody_modification",
                    "requested_custody_arrangement": "sole custody",
                    "change_reason": "Parent relocated",
                    "is_emergency": False,
                    "party_name": "Jane Smith",
                    "other_party_name": "John Doe",
                    "case_number": "FL-2024-001",
                    "children_info": [
                        {"name": "Alice Smith", "dob": "2015-01-15"},
                        {"name": "Bob Smith", "dob": "2017-03-20"}
                    ]
                }
                self.messages = []

        from app.services.chat_to_pdf_service import ChatToPDFService

        service = ChatToPDFService()

        # Test extracting conversation data
        session = MockChatSession()
        data = service._extract_conversation_data(session)

        print(f"✓ Extracted Conversation Data:")
        print(f"  Motion type: {data.get('motion_type_detected')}")
        print(f"  Children: {len(data.get('children_info', []))}")

        # Test determining motion type
        motion_type = service._determine_motion_type(data, session)
        print(f"\n✓ Determined Motion Type: {motion_type}")

        # Test getting required forms
        forms = service._get_required_forms(motion_type, data)
        print(f"\n✓ Required Forms: {forms}")

        # Test creating confirmation summary
        mock_db = MockDB()
        summary = await service.create_confirmation_summary(mock_db, "test-session")
        print(f"\n✓ Confirmation Summary Generated")

        return True
    except Exception as e:
        print(f"✗ Chat to PDF Integration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all tests"""
    print("=" * 60)
    print("CHAT TO PDF WORKFLOW TEST")
    print("=" * 60)

    results = []

    # Run tests
    results.append(("LLM Chat Service", await test_llm_chat_service()))
    results.append(("Question Graph", await test_question_graph()))
    results.append(("Form Mapper", await test_form_mapper()))
    results.append(("Memory Service", await test_memory_service()))
    results.append(("Chat to PDF Integration", await test_chat_to_pdf_integration()))

    # Print summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status} - {name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
    else:
        print(f"\n⚠️ {total - passed} tests failed")

    return passed == total

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)