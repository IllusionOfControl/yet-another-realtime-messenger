import pytest
from unittest.mock import patch

@pytest.mark.asyncio
async def test_user_service_404_format(client):
    response = await client.get("/api/v1/users/invalid/path")
    assert response.status_code == 404
    data = response.json()
    assert data["error"]["code"] == "HTTP_ERROR"
    assert "trace_id" in data["error"]

@pytest.mark.asyncio
async def test_user_service_validation_format(client):
    response = await client.post("/api/v1/users/internal/create-profile", json={"username": "hi"})
    assert response.status_code == 422
    data = response.json()
    assert data["error"]["code"] == "VALIDATION_ERROR"
    assert len(data["error"]["details"]) > 0

@pytest.mark.asyncio
async def test_user_service_500_masking(client):
    with patch("app.api.get_user_profile_by_id", side_effect=RuntimeError("Connection Lost")):
        fake_id = "00000000-0000-0000-0000-000000000000"
        with patch("app.api.require_permission", return_value=lambda: True):
            response = await client.get(f"/api/v1/users/{fake_id}")
            
    assert response.status_code == 500
    data = response.json()
    assert data["error"]["code"] == "INTERNAL_SERVER_ERROR"
    assert "Connection Lost" not in data["error"]["message"]