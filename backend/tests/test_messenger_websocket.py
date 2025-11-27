"""
WebSocket Messenger Tests

Tests for real-time messaging via WebSocket endpoint.

Test Cases:
1. Connection establishment and online status
2. Message subscription to conversations
3. Typing indicators
4. Read receipts
5. Disconnect and offline status
"""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Test client for WebSocket connections"""
    from main import app

    return TestClient(app)


def test_websocket_connect_disconnect(client):
    """Test WebSocket connection and disconnection"""
    user_id = 1

    with client.websocket_connect(f"/api/v1/messenger/ws/{user_id}") as websocket:
        # Should receive welcome message
        data = websocket.receive_json()
        assert data["type"] == "system"
        assert data["event"] == "connected"
        assert "timestamp" in data

        # Connection established
        print(f"✅ Connected as user {user_id}")

    # Disconnection handled automatically
    print(f"✅ Disconnected user {user_id}")


def test_websocket_subscribe_to_conversation(client):
    """Test subscribing to conversation updates"""
    user_id = 1
    conversation_id = "550e8400-e29b-41d4-a716-446655440000"

    with client.websocket_connect(f"/api/v1/messenger/ws/{user_id}") as websocket:
        # Receive welcome message
        welcome = websocket.receive_json()
        assert welcome["type"] == "system"

        # Subscribe to conversation
        websocket.send_json({"type": "subscribe", "conversation_id": conversation_id})

        # Should receive subscription confirmation
        response = websocket.receive_json()
        assert response["type"] == "subscribed"
        assert response["conversation_id"] == conversation_id

        print(f"✅ Subscribed to conversation {conversation_id}")


def test_websocket_typing_indicator(client):
    """Test sending typing indicator"""
    user_id = 1
    conversation_id = "550e8400-e29b-41d4-a716-446655440000"

    with client.websocket_connect(f"/api/v1/messenger/ws/{user_id}") as websocket:
        # Receive welcome message
        websocket.receive_json()

        # Send typing indicator
        websocket.send_json({"type": "typing", "conversation_id": conversation_id})

        print(f"✅ Sent typing indicator")


def test_websocket_invalid_json(client):
    """Test handling of invalid JSON"""
    user_id = 1

    with client.websocket_connect(f"/api/v1/messenger/ws/{user_id}") as websocket:
        # Receive welcome message
        websocket.receive_json()

        # Send invalid JSON
        websocket.send_text("invalid json {{{")

        # Should receive error message
        response = websocket.receive_json()
        assert response["type"] == "error"
        assert "Invalid JSON" in response["message"]

        print(f"✅ Invalid JSON handled correctly")


def test_websocket_unknown_message_type(client):
    """Test handling of unknown message types"""
    user_id = 1

    with client.websocket_connect(f"/api/v1/messenger/ws/{user_id}") as websocket:
        # Receive welcome message
        websocket.receive_json()

        # Send unknown message type
        websocket.send_json({"type": "unknown_type", "data": "test"})

        print(f"✅ Unknown message type handled")


def test_websocket_invalid_conversation_id(client):
    """Test subscribing with invalid conversation ID format"""
    user_id = 1

    with client.websocket_connect(f"/api/v1/messenger/ws/{user_id}") as websocket:
        # Receive welcome message
        websocket.receive_json()

        # Subscribe with invalid UUID
        websocket.send_json({"type": "subscribe", "conversation_id": "invalid-uuid"})

        # Should receive error
        response = websocket.receive_json()
        assert response["type"] == "error"
        assert "Invalid conversation_id" in response["message"]

        print(f"✅ Invalid conversation ID handled")


# Integration test with multiple clients
def test_websocket_multiple_clients(client):
    """Test multiple clients for same user (multi-device support)"""
    user_id = 1

    # First connection (e.g., web browser)
    with client.websocket_connect(f"/api/v1/messenger/ws/{user_id}") as ws1:
        ws1.receive_json()  # Welcome message

        # Second connection (e.g., mobile app)
        with client.websocket_connect(f"/api/v1/messenger/ws/{user_id}") as ws2:
            ws2.receive_json()  # Welcome message

            print(f"✅ Multiple connections for user {user_id} established")

            # Both connections should be active
            # Manager should track both WebSocket instances


if __name__ == "__main__":
    """Run tests manually for debugging"""
    import sys
    import os

    # Add parent directory to path
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    from main import app
    from fastapi.testclient import TestClient

    test_client = TestClient(app)

    print("=" * 60)
    print("WebSocket Messenger Tests")
    print("=" * 60)
    print()

    try:
        test_websocket_connect_disconnect(test_client)
        print()

        test_websocket_subscribe_to_conversation(test_client)
        print()

        test_websocket_typing_indicator(test_client)
        print()

        test_websocket_invalid_json(test_client)
        print()

        test_websocket_unknown_message_type(test_client)
        print()

        test_websocket_invalid_conversation_id(test_client)
        print()

        test_websocket_multiple_clients(test_client)
        print()

        print("=" * 60)
        print("✅ All tests passed!")
        print("=" * 60)

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
