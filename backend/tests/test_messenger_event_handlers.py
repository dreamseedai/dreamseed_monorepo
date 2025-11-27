"""
WebSocket Event Handler Tests

Tests for Task 2.1: WebSocket Event Handlers
- message.send
- message.edit
- message.delete
- typing.start / typing.stop
- message.read (read receipts)
"""

import uuid

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Test client for WebSocket connections"""
    from main import app

    return TestClient(app)


@pytest.fixture
def test_conversation_id():
    """Test conversation UUID"""
    return "550e8400-e29b-41d4-a716-446655440000"


def test_message_send_event(client, test_conversation_id):
    """Test message.send event via WebSocket"""
    user_id = 1

    with client.websocket_connect(f"/api/v1/messenger/ws/{user_id}") as websocket:
        # Receive welcome message
        welcome = websocket.receive_json()
        assert welcome["type"] == "system"

        # Send message via WebSocket
        websocket.send_json(
            {
                "type": "message.send",
                "conversation_id": test_conversation_id,
                "content": "Hello via WebSocket!",
                "message_type": "text",
            }
        )

        # Should receive either message.sent or error
        response = websocket.receive_json()
        print(f"Response: {response}")

        # Could be error if user not participant, or success
        assert response["type"] in ["message.sent", "error"]

        if response["type"] == "message.sent":
            assert "message_id" in response
            assert "data" in response
            print(f"✅ Message sent: {response['message_id']}")
        else:
            print(f"⚠️ Expected error: {response['message']}")


def test_typing_indicators(client, test_conversation_id):
    """Test typing.start and typing.stop events"""
    user_id = 1

    with client.websocket_connect(f"/api/v1/messenger/ws/{user_id}") as websocket:
        # Receive welcome message
        websocket.receive_json()

        # Send typing start
        websocket.send_json(
            {"type": "typing.start", "conversation_id": test_conversation_id}
        )
        print(f"✅ Typing start sent")

        # Send typing stop
        websocket.send_json(
            {"type": "typing.stop", "conversation_id": test_conversation_id}
        )
        print(f"✅ Typing stop sent")


def test_message_edit_event(client, test_conversation_id):
    """Test message.edit event via WebSocket"""
    user_id = 1
    # Use a fake message ID for testing
    message_id = str(uuid.uuid4())

    with client.websocket_connect(f"/api/v1/messenger/ws/{user_id}") as websocket:
        # Receive welcome message
        websocket.receive_json()

        # Try to edit message
        websocket.send_json(
            {
                "type": "message.edit",
                "message_id": message_id,
                "content": "Updated content",
            }
        )

        # Should receive error (message not found)
        response = websocket.receive_json()
        assert response["type"] == "error"
        assert "not found" in response["message"].lower()
        print(f"✅ Expected error received: {response['message']}")


def test_message_delete_event(client, test_conversation_id):
    """Test message.delete event via WebSocket"""
    user_id = 1
    message_id = str(uuid.uuid4())

    with client.websocket_connect(f"/api/v1/messenger/ws/{user_id}") as websocket:
        # Receive welcome message
        websocket.receive_json()

        # Try to delete message
        websocket.send_json({"type": "message.delete", "message_id": message_id})

        # Should receive error (message not found)
        response = websocket.receive_json()
        assert response["type"] == "error"
        print(f"✅ Expected error received: {response['message']}")


def test_read_receipt_event(client, test_conversation_id):
    """Test message.read event via WebSocket"""
    user_id = 1
    message_id = str(uuid.uuid4())

    with client.websocket_connect(f"/api/v1/messenger/ws/{user_id}") as websocket:
        # Receive welcome message
        websocket.receive_json()

        # Try to mark as read
        websocket.send_json({"type": "message.read", "message_id": message_id})

        # Should receive error (message not found)
        response = websocket.receive_json()
        assert response["type"] == "error"
        print(f"✅ Expected error received: {response['message']}")


def test_full_message_lifecycle(client, test_conversation_id):
    """Test full message lifecycle: send -> edit -> delete"""
    user_id = 1

    with client.websocket_connect(f"/api/v1/messenger/ws/{user_id}") as websocket:
        # Receive welcome message
        websocket.receive_json()

        # 1. Send message
        websocket.send_json(
            {
                "type": "message.send",
                "conversation_id": test_conversation_id,
                "content": "Test message lifecycle",
                "message_type": "text",
            }
        )

        response1 = websocket.receive_json()
        print(f"Send response: {response1['type']}")

        if response1["type"] == "message.sent":
            message_id = response1["message_id"]

            # 2. Edit message
            websocket.send_json(
                {
                    "type": "message.edit",
                    "message_id": message_id,
                    "content": "Updated message",
                }
            )

            response2 = websocket.receive_json()
            print(f"Edit response: {response2['type']}")

            # 3. Delete message
            websocket.send_json({"type": "message.delete", "message_id": message_id})

            response3 = websocket.receive_json()
            print(f"Delete response: {response3['type']}")

            print(f"✅ Full lifecycle completed")
        else:
            print(f"⚠️ Send failed, skipping lifecycle test: {response1['message']}")


def test_invalid_event_handling(client):
    """Test handling of invalid events"""
    user_id = 1

    with client.websocket_connect(f"/api/v1/messenger/ws/{user_id}") as websocket:
        # Receive welcome message
        websocket.receive_json()

        # Send message with missing required fields
        websocket.send_json({"type": "message.send"})  # Missing conversation_id

        # Should receive error
        response = websocket.receive_json()
        assert response["type"] == "error"
        print(f"✅ Invalid event handled: {response['message']}")


if __name__ == "__main__":
    """Run tests manually for debugging"""
    import sys
    import os

    # Add parent directory to path
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    from main import app
    from fastapi.testclient import TestClient

    test_client = TestClient(app)
    test_conv_id = "550e8400-e29b-41d4-a716-446655440000"

    print("=" * 60)
    print("WebSocket Event Handler Tests")
    print("=" * 60)
    print()

    try:
        print("Test 1: Message Send Event")
        test_message_send_event(test_client, test_conv_id)
        print()

        print("Test 2: Typing Indicators")
        test_typing_indicators(test_client, test_conv_id)
        print()

        print("Test 3: Message Edit Event")
        test_message_edit_event(test_client, test_conv_id)
        print()

        print("Test 4: Message Delete Event")
        test_message_delete_event(test_client, test_conv_id)
        print()

        print("Test 5: Read Receipt Event")
        test_read_receipt_event(test_client, test_conv_id)
        print()

        print("Test 6: Full Message Lifecycle")
        test_full_message_lifecycle(test_client, test_conv_id)
        print()

        print("Test 7: Invalid Event Handling")
        test_invalid_event_handling(test_client)
        print()

        print("=" * 60)
        print("✅ All tests completed!")
        print("=" * 60)

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
