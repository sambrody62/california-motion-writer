#!/usr/bin/env python3
"""
Test script for enhanced LLM chat functionality
"""
import asyncio
import json
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.llm_chat_service import llm_chat_service
from app.services.question_graph_service import question_graph
from app.services.form_field_mapper import form_mapper
from app.models.chat import ChatSessionState

async def test_intent_classification():
    """Test LLM intent classification"""
    print("\n=== Testing Intent Classification ===\n")

    test_messages = [
        "I need to file for custody of my children",
        "My ex isn't paying child support",
        "I received court papers and need to respond",
        "Can you help me understand what a restraining order is?",
        "My ex violated our custody agreement",
        "Hello, I need help",
        "I want to change our visitation schedule"
    ]

    for message in test_messages:
        print(f"Message: '{message}'")
        intent, entities, confidence = await llm_chat_service.classify_intent(message)
        print(f"  Intent: {intent} (confidence: {confidence:.2f})")
        print(f"  Entities: {json.dumps(entities, indent=2)}")
        print()

async def test_contextual_response():
    """Test contextual response generation"""
    print("\n=== Testing Contextual Response Generation ===\n")

    test_cases = [
        {
            "state": ChatSessionState.GREETING,
            "message": "I need help with custody",
            "intent": "FILE_MOTION",
            "entities": {"motion_type": "custody"},
            "context": {}
        },
        {
            "state": ChatSessionState.MOTION_SELECTION,
            "message": "I want to modify our existing custody order",
            "intent": "MODIFY_ORDER",
            "entities": {"motion_type": "custody"},
            "context": {"user_name": "John Doe", "case_number": "FL-2024-001"}
        },
        {
            "state": ChatSessionState.INFORMATION_GATHERING,
            "message": "We currently have joint custody",
            "intent": "PROVIDE_INFO",
            "entities": {"current_custody": "joint"},
            "context": {"motion_type": "custody", "modification": True}
        }
    ]

    for i, test in enumerate(test_cases, 1):
        print(f"Test Case {i}:")
        print(f"  State: {test['state'].value}")
        print(f"  User: '{test['message']}'")

        response, quick_replies = await llm_chat_service.generate_contextual_response(
            test["state"],
            test["message"],
            test["intent"],
            test["entities"],
            test["context"]
        )

        print(f"  Assistant: {response}")
        print(f"  Quick Replies: {quick_replies}")
        print()

async def test_question_graph():
    """Test dynamic question flow"""
    print("\n=== Testing Question Graph ===\n")

    motion_type = "custody_modification"
    answered = {}
    profile = {"case_number": "FL-2024-001"}

    print(f"Motion Type: {motion_type}")
    print(f"Profile Data: {profile}")
    print("\nQuestion Flow:")

    for i in range(10):  # Limit iterations
        next_q = question_graph.get_next_question(motion_type, answered, profile)

        if not next_q:
            print("\n✓ All required questions answered!")
            break

        print(f"\n{i+1}. {next_q.text}")
        print(f"   Field: {next_q.field_name}")
        print(f"   Type: {next_q.question_type.value}")
        print(f"   Priority: {next_q.priority}")

        # Simulate answer
        if next_q.data_type == "boolean":
            answer = True if i % 2 == 0 else False
        elif next_q.data_type == "number":
            answer = 1500 + (i * 100)
        elif next_q.data_type == "date":
            answer = "01/15/2024"
        else:
            answer = f"Sample answer for {next_q.field_name}"

        answered[next_q.field_name] = answer
        print(f"   → Answer: {answer}")

    # Check completeness
    is_complete, missing = question_graph.validate_completeness(motion_type, answered)
    print(f"\nCompleteness Check: {'✓ Complete' if is_complete else '✗ Incomplete'}")
    if missing:
        print(f"Missing Fields: {missing}")

    # Generate summary
    print("\nGenerated Summary:")
    print(question_graph.generate_summary(answered))

async def test_form_mapping():
    """Test conversation to form field mapping"""
    print("\n=== Testing Form Field Mapping ===\n")

    conversation_data = {
        "party_name": "Jane Smith",
        "other_party_name": "John Smith",
        "case_number": "FL-2024-001",
        "requested_custody_arrangement": "Sole legal and physical custody",
        "current_custody_arrangement": "Joint legal and physical custody",
        "change_reason": "Other parent has been absent for 6 months",
        "is_emergency": False,
        "current_support_amount": 1500,
        "requested_support_amount": 2000,
        "children_info": {
            "names": ["Alice Smith", "Bob Smith"],
            "birthdates": ["01/15/2015", "03/20/2017"]
        }
    }

    form_types = ["FL-300", "FL-311", "MC-030"]

    for form_type in form_types:
        print(f"\nForm: {form_type}")

        # Map fields
        mapped_fields = form_mapper.map_conversation_to_form(
            form_type,
            conversation_data
        )

        print(f"Mapped Fields ({len(mapped_fields)}):")
        for field, value in list(mapped_fields.items())[:5]:  # Show first 5
            print(f"  {field}: {value}")

        # Validate
        is_valid, missing = form_mapper.validate_required_fields(form_type, mapped_fields)
        print(f"Validation: {'✓ Valid' if is_valid else '✗ Invalid'}")
        if missing:
            print(f"  Missing: {missing}")

        # Get missing info
        missing_info = form_mapper.get_missing_information(form_type, conversation_data)
        if missing_info:
            print(f"Questions for missing info:")
            for info in missing_info[:3]:  # Show first 3
                print(f"  - {info['question']}")

async def test_field_extraction():
    """Test extracting form fields from conversation"""
    print("\n=== Testing Field Extraction from Conversation ===\n")

    conversation = [
        {"sender": "assistant", "content": "Hello! How can I help you today?"},
        {"sender": "user", "content": "I need to modify our custody agreement. My ex-husband John hasn't seen the kids in 6 months."},
        {"sender": "assistant", "content": "I understand you want to modify custody. What's your current arrangement?"},
        {"sender": "user", "content": "We have joint custody, but I want sole custody now. The kids are Alice (9) and Bob (7)."},
        {"sender": "assistant", "content": "What's your case number?"},
        {"sender": "user", "content": "It's FL-2024-001"},
    ]

    print("Conversation:")
    for msg in conversation:
        print(f"  {msg['sender']}: {msg['content']}")

    print("\nExtracting fields for FL-300...")
    extracted = await llm_chat_service.extract_form_fields(conversation, "FL-300")

    print("Extracted Fields:")
    for field, value in extracted.items():
        print(f"  {field}: {value}")

async def main():
    """Run all tests"""
    print("=" * 60)
    print("Enhanced LLM Chat System Tests")
    print("=" * 60)

    try:
        # Test each component
        await test_intent_classification()
        await test_contextual_response()
        await test_question_graph()
        await test_form_mapping()
        await test_field_extraction()

        print("\n" + "=" * 60)
        print("✓ All tests completed successfully!")
        print("=" * 60)

    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())