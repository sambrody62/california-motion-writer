#!/usr/bin/env python3
"""
Test script for chat WebSocket connection and API endpoints
"""
import asyncio
import json
import httpx
import websockets
from datetime import datetime

# Configuration
API_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000/ws"

# Test credentials
TEST_USER = {
    "email": "test@example.com",
    "password": "testpass123",
    "full_name": "Test User"
}

async def test_api_endpoints():
    """Test REST API endpoints"""
    print("\n=== Testing REST API Endpoints ===")

    async with httpx.AsyncClient() as client:
        # 1. Register user
        print("\n1. Registering user...")
        try:
            response = await client.post(
                f"{API_URL}/api/v1/auth/register",
                json=TEST_USER
            )
            if response.status_code == 200:
                token_data = response.json()
                token = token_data["access_token"]
                print(f"✓ User registered, token: {token[:20]}...")
            elif response.status_code == 400:
                # User might already exist, try login
                print("User exists, attempting login...")
                response = await client.post(
                    f"{API_URL}/api/v1/auth/token",
                    data={
                        "username": TEST_USER["email"],
                        "password": TEST_USER["password"]
                    }
                )
                token_data = response.json()
                token = token_data["access_token"]
                print(f"✓ Logged in, token: {token[:20]}...")
        except Exception as e:
            print(f"✗ Auth failed: {e}")
            return None

        headers = {"Authorization": f"Bearer {token}"}

        # 2. Create chat session
        print("\n2. Creating chat session...")
        response = await client.post(
            f"{API_URL}/api/v1/chat/sessions",
            headers=headers,
            json={"initial_message": "I need help filing a custody motion"}
        )
        if response.status_code == 200:
            session_data = response.json()
            session_id = session_data["session_id"]
            print(f"✓ Session created: {session_id}")
        else:
            print(f"✗ Failed to create session: {response.status_code}")
            return None

        # 3. Send message via REST
        print("\n3. Sending message via REST...")
        response = await client.post(
            f"{API_URL}/api/v1/chat/messages",
            headers=headers,
            json={
                "session_id": session_id,
                "content": "I want to modify an existing custody order"
            }
        )
        if response.status_code == 200:
            print("✓ Message sent and processed")
            print(f"Response: {response.json()}")
        else:
            print(f"✗ Failed to send message: {response.status_code}")

        # 4. Get message history
        print("\n4. Fetching message history...")
        response = await client.get(
            f"{API_URL}/api/v1/chat/sessions/{session_id}/messages",
            headers=headers
        )
        if response.status_code == 200:
            history = response.json()
            print(f"✓ Retrieved {history['total_count']} messages")
        else:
            print(f"✗ Failed to get history: {response.status_code}")

        return token, session_id

async def test_websocket(token: str, session_id: str = None):
    """Test WebSocket connection"""
    print("\n=== Testing WebSocket Connection ===")

    try:
        async with websockets.connect(WS_URL) as websocket:
            # 1. Send authentication
            print("\n1. Authenticating WebSocket...")
            auth_message = {
                "type": "connect",
                "data": {
                    "token": token,
                    "session_id": session_id
                }
            }
            await websocket.send(json.dumps(auth_message))

            # Wait for connection confirmation
            response = await websocket.recv()
            data = json.loads(response)
            if data["type"] == "connected":
                print(f"✓ WebSocket connected: {data['data']}")
            else:
                print(f"✗ Unexpected response: {data}")
                return

            # 2. Send a message
            print("\n2. Sending message via WebSocket...")
            message = {
                "type": "message",
                "data": {
                    "content": "What documents do I need for a custody modification?"
                }
            }
            await websocket.send(json.dumps(message))
            print("✓ Message sent")

            # 3. Receive responses
            print("\n3. Waiting for responses...")
            timeout = 10  # seconds
            start_time = asyncio.get_event_loop().time()

            while asyncio.get_event_loop().time() - start_time < timeout:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    data = json.loads(response)

                    if data["type"] == "assistant_typing":
                        print(f"  Assistant typing: {data['data']['typing']}")
                    elif data["type"] == "message":
                        print(f"✓ Assistant response received:")
                        print(f"  Content: {data['data']['content'][:100]}...")
                        if data['data'].get('quick_replies'):
                            print(f"  Quick replies: {data['data']['quick_replies']}")
                    elif data["type"] == "session_update":
                        print(f"  Session updated: State={data['data']['state']}")
                    else:
                        print(f"  Other message: {data['type']}")

                except asyncio.TimeoutError:
                    continue
                except websockets.exceptions.ConnectionClosed:
                    print("WebSocket connection closed")
                    break

            # 4. Test ping/pong
            print("\n4. Testing heartbeat...")
            await websocket.send(json.dumps({"type": "ping"}))
            response = await websocket.recv()
            data = json.loads(response)
            if data["type"] == "pong":
                print("✓ Heartbeat working")

    except Exception as e:
        print(f"✗ WebSocket error: {e}")

async def main():
    """Run all tests"""
    print("Starting Chat System Tests")
    print("=" * 50)

    # Test REST API
    result = await test_api_endpoints()

    if result:
        token, session_id = result

        # Test WebSocket
        await test_websocket(token, session_id)

    print("\n" + "=" * 50)
    print("Tests completed!")

if __name__ == "__main__":
    asyncio.run(main())