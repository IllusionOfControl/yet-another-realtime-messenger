import pytest
import json
from app.manager import manager

@pytest.mark.asyncio
async def test_presence_updates_in_redis(client, jwt_token_factory, mock_redis):
    user_id = "user-presence-test"
    token = jwt_token_factory(user_id)
    
    with client.websocket_connect(f"/ws?token={token}"):
        # Verify Redis 'set' was called on connect
        mock_redis.set.assert_called_with(f"presence:{user_id}", "online", ex=300)
    
    # Verify Redis 'delete' was called on disconnect (context manager exit)
    mock_redis.delete.assert_called_with(f"presence:{user_id}")

@pytest.mark.asyncio
async def test_message_delivery_to_active_connection(client, jwt_token_factory):
    user_id = "user-delivery-test"
    token = jwt_token_factory(user_id)
    test_payload = {"type": "new_message", "data": {"text": "hello"}}

    with client.websocket_connect(f"/ws?token={token}") as websocket:
        # Manually trigger the manager to send a message to this user
        await manager.send_personal_message(user_id, test_payload)
        
        # Receive and verify
        received_data = websocket.receive_json()
        assert received_data == test_payload
