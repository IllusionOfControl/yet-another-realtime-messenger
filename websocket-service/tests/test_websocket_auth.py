import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

def test_websocket_rejects_invalid_token(client: TestClient):
    with pytest.raises(WebSocketDisconnect) as exc:
        with client.websocket_connect("/ws?token=invalid-token"):
            pass
    # code 1008 is Policy Violation
    assert exc.value.code == 1008

def test_websocket_accepts_valid_token(client: TestClient, jwt_token_factory):
    user_id = "user-123"
    token = jwt_token_factory(user_id)
    with client.websocket_connect(f"/ws?token={token}") as websocket:
        # If we reach here, connection was accepted
        assert True 
