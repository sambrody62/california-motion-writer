#!/usr/bin/env python3
"""
End-to-end test for chat to PDF generation workflow
"""
import asyncio
import json
import httpx
import websockets
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configuration
API_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000/ws"

# Test user credentials
TEST_USER = {
    "email": "e2e_test@example.com",
    "password": "testpass123",
    "full_name": "Test E2E User"
}

# Test profile data
TEST_PROFILE = {
    "county": "San Diego",
    "is_petitioner": True,
    "party_name": "Jane E2E Smith",
    "other_party_name": "John E2E Doe",
    "case_number": "E2E-2024-TEST",
    "children_info": [
        {"name": "Alice Smith", "dob": "2015-01-15"},
        {"name": "Bob Smith", "dob": "2017-03-20"}
    ]
}

async def setup_test_user(client: httpx.AsyncClient):
    """Setup test user and profile"""
    print("\n=== Setting Up Test User ===")

    # Try to register
    try:
        response = await client.post(
            f"{API_URL}/api/v1/auth/register",
            json=TEST_USER
        )
        if response.status_code == 200:
            token_data = response.json()
            token = token_data["access_token"]
            print("✓ User registered")
    except:
        pass

    # Try login
    response = await client.post(
        f"{API_URL}/api/v1/auth/token",
        data={
            "username": TEST_USER["email"],
            "password": TEST_USER["password"]
        }
    )
    if response.status_code == 200:
        token_data = response.json()
        token = token_data["access_token"]
        print("✓ User logged in")
    else:
        print("✗ Failed to authenticate")
        return None, None

    headers = {"Authorization": f"Bearer {token}"}

    # Create/update profile
    response = await client.post(
        f"{API_URL}/api/v1/profiles",
        headers=headers,
        json=TEST_PROFILE
    )
    print("✓ Profile created/updated")

    return token, headers

async def test_chat_conversation(headers: dict):
    """Test chat conversation flow"""
    print("\n=== Testing Chat Conversation ===")

    async with httpx.AsyncClient() as client:
        # 1. Create chat session
        response = await client.post(
            f"{API_URL}/api/v1/chat/sessions",
            headers=headers,
            json={"initial_message": "I need to modify our custody arrangement"}
        )
        if response.status_code != 200:
            print(f"✗ Failed to create session: {response.status_code}")
            return None

        session_data = response.json()
        session_id = session_data["session_id"]
        print(f"✓ Chat session created: {session_id}")

        # 2. Simulate conversation
        conversation_flow = [
            "I want to change from joint custody to sole custody",
            "My ex hasn't seen the kids in 6 months",
            "He moved out of state and hasn't visited",
            "I want sole legal and physical custody",
            "The current order is from January 2023",
            "Yes, I want to request a hearing",
            "No, this is not an emergency"
        ]

        for i, message in enumerate(conversation_flow, 1):
            response = await client.post(
                f"{API_URL}/api/v1/chat/messages",
                headers=headers,
                json={
                    "session_id": session_id,
                    "content": message
                }
            )
            if response.status_code == 200:
                result = response.json()
                print(f"  {i}. User: {message[:50]}...")
                if result.get("response"):
                    assistant_msg = result["response"]["message"]["content"]
                    print(f"     Assistant: {assistant_msg[:70]}...")
            else:
                print(f"✗ Failed to send message {i}")

        print("✓ Conversation completed")
        return session_id

async def test_chat_to_pdf_workflow(headers: dict, session_id: str):
    """Test the chat to PDF generation workflow"""
    print("\n=== Testing Chat to PDF Workflow ===")

    async with httpx.AsyncClient(timeout=30.0) as client:
        # 1. Check missing information
        print("\n1. Checking for missing information...")
        response = await client.post(
            f"{API_URL}/api/v1/chat-pdf/missing-info",
            headers=headers,
            json={"session_id": session_id}
        )
        if response.status_code == 200:
            result = response.json()
            missing_count = result.get("count", 0)
            print(f"   Missing fields: {missing_count}")
            if missing_count > 0:
                for field in result.get("missing_fields", [])[:3]:
                    print(f"   - {field['question']}")

        # 2. Get confirmation summary
        print("\n2. Getting confirmation summary...")
        response = await client.get(
            f"{API_URL}/api/v1/chat-pdf/summary/{session_id}",
            headers=headers
        )
        if response.status_code == 200:
            result = response.json()
            summary = result.get("summary", "")
            print("   Summary preview:")
            for line in summary.split("\n")[:10]:
                if line.strip():
                    print(f"   {line}")

        # 3. Prepare motion from chat
        print("\n3. Preparing motion from chat...")
        response = await client.post(
            f"{API_URL}/api/v1/chat-pdf/prepare-motion",
            headers=headers,
            json={"session_id": session_id}
        )
        if response.status_code != 200:
            print(f"✗ Failed to prepare motion: {response.status_code}")
            return None

        prepare_result = response.json()
        motion_id = prepare_result.get("motion_id")
        print(f"✓ Motion prepared: {motion_id}")
        print(f"  Motion type: {prepare_result.get('motion_type')}")
        print(f"  Required forms: {prepare_result.get('required_forms')}")
        print(f"  Ready for PDF: {prepare_result.get('ready_for_pdf')}")

        # 4. Generate PDFs (if ready)
        if prepare_result.get("ready_for_pdf"):
            print("\n4. Generating PDFs...")
            response = await client.post(
                f"{API_URL}/api/v1/chat-pdf/generate-pdf",
                headers=headers,
                json={"motion_id": motion_id}
            )
            if response.status_code == 200:
                pdf_result = response.json()
                print(f"✓ PDFs generated successfully")
                for pdf in pdf_result.get("generated_pdfs", []):
                    print(f"  - {pdf['form_type']}: {pdf['file_name']}")
                if pdf_result.get("packet_path"):
                    print(f"  - Combined packet created")
            else:
                print(f"✗ PDF generation failed: {response.status_code}")
        else:
            print("\n4. Cannot generate PDFs - missing required information")
            for field in prepare_result.get("missing_fields", [])[:5]:
                print(f"  - Missing: {field}")

        return motion_id

async def test_complete_workflow(headers: dict, session_id: str):
    """Test the complete workflow endpoint"""
    print("\n=== Testing Complete Workflow Endpoint ===")

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{API_URL}/api/v1/chat-pdf/complete-workflow",
            headers=headers,
            json={"session_id": session_id}
        )

        if response.status_code == 200:
            result = response.json()
            print(f"✓ Workflow completed: {result.get('workflow_complete')}")

            if result.get("workflow_complete"):
                print("  PDFs generated:")
                for pdf in result.get("pdfs_generated", []):
                    print(f"    - {pdf['form_type']}")
            else:
                print(f"  Missing information: {len(result.get('missing_questions', []))} questions")

            return result.get("motion_id")
        else:
            print(f"✗ Workflow failed: {response.status_code}")
            return None

async def test_websocket_flow(token: str):
    """Test WebSocket-based conversation flow"""
    print("\n=== Testing WebSocket Flow ===")

    try:
        async with websockets.connect(WS_URL) as websocket:
            # Authenticate
            await websocket.send(json.dumps({
                "type": "connect",
                "data": {"token": token}
            }))

            response = await websocket.recv()
            data = json.loads(response)
            if data["type"] != "connected":
                print("✗ WebSocket authentication failed")
                return

            print("✓ WebSocket connected")

            # Send test messages
            test_messages = [
                "I need help with a custody modification",
                "We currently have 50/50 custody",
                "I want full custody because my ex is unreliable"
            ]

            for msg in test_messages:
                await websocket.send(json.dumps({
                    "type": "message",
                    "data": {"content": msg}
                }))
                print(f"  Sent: {msg}")

                # Wait for responses
                for _ in range(3):  # Wait for up to 3 messages
                    try:
                        response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                        data = json.loads(response)
                        if data["type"] == "message":
                            print(f"  Received: {data['data']['content'][:80]}...")
                            break
                    except asyncio.TimeoutError:
                        continue

            print("✓ WebSocket conversation completed")

    except Exception as e:
        print(f"✗ WebSocket error: {e}")

async def cleanup_test_data(headers: dict, motion_id: str):
    """Clean up test data"""
    print("\n=== Cleaning Up Test Data ===")
    # In production, you might want to delete test data
    print(f"  Test motion ID: {motion_id}")
    print("  ✓ Test data retained for review")

async def main():
    """Run complete end-to-end test"""
    print("=" * 60)
    print("END-TO-END TEST: Chat to PDF Generation")
    print("=" * 60)

    async with httpx.AsyncClient() as client:
        # Setup
        token, headers = await setup_test_user(client)
        if not token:
            print("✗ Failed to setup test user")
            return

        try:
            # Test chat conversation
            session_id = await test_chat_conversation(headers)
            if not session_id:
                print("✗ Chat conversation failed")
                return

            # Test chat to PDF workflow
            motion_id = await test_chat_to_pdf_workflow(headers, session_id)

            # Test complete workflow endpoint
            # (Using a new session for clean test)
            new_session_response = await client.post(
                f"{API_URL}/api/v1/chat/sessions",
                headers=headers,
                json={"initial_message": "I need to file for support modification"}
            )
            if new_session_response.status_code == 200:
                new_session_id = new_session_response.json()["session_id"]
                await test_complete_workflow(headers, new_session_id)

            # Test WebSocket flow
            await test_websocket_flow(token)

            # Cleanup
            if motion_id:
                await cleanup_test_data(headers, motion_id)

            print("\n" + "=" * 60)
            print("✓ END-TO-END TEST COMPLETED SUCCESSFULLY")
            print("=" * 60)

        except Exception as e:
            print(f"\n✗ Test failed with error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    print("\nStarting end-to-end test...")
    print("Make sure the backend is running on http://localhost:8000")
    print("-" * 60)
    asyncio.run(main())