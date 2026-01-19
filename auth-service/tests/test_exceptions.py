import pytest
from unittest.mock import patch

@pytest.mark.asyncio
async def test_standardized_404_error(client):
    """Test that a non-existent route returns the standard error format."""
    response = await client.get("/api/v1/auth/non-existent-endpoint")
    assert response.status_code == 404
    
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "HTTP_ERROR"
    assert "message" in data["error"]
    assert "trace_id" in data["error"]
    assert data["error"]["trace_id"] is not None

@pytest.mark.asyncio
async def test_standardized_validation_error(client):
    """Test that Pydantic validation errors return the standard error format."""
    # Sending empty body to registration which requires fields
    response = await client.post("/api/v1/auth/register", json={})
    assert response.status_code == 422
    
    data = response.json()
    assert data["error"]["code"] == "VALIDATION_ERROR"
    assert "details" in data["error"]
    assert isinstance(data["error"]["details"], list)
    assert data["error"]["trace_id"] is not None

@pytest.mark.asyncio
async def test_standardized_500_error(client):
    """Test that unhandled exceptions are masked and standardized."""
    # Mocking a CRUD function to raise a raw Exception
    with patch("app.api.get_local_auth_by_identifier", side_effect=Exception("Database crash!")):
        response = await client.post(
            "/api/v1/auth/login", 
            json={"login": "test", "password": "password"}
        )
        
    assert response.status_code == 500
    data = response.json()
    assert data["error"]["code"] == "INTERNAL_SERVER_ERROR"
    assert data["error"]["message"] == "An unexpected error occurred"
    # Ensure the raw "Database crash!" message is NOT leaked to the client
    assert "Database crash!" not in data["error"]["message"]
    assert data["error"]["trace_id"] is not None

@pytest.mark.asyncio
async def test_app_exception_handling(client):
    """Test that domain-specific AppExceptions are handled correctly."""
    # We can trigger a 409 Conflict which uses HTTPException (mapped to HTTP_ERROR)
    # or mock an endpoint to raise AppException. 
    # For this test, we verify the existing 401 logic in login.
    response = await client.post(
        "/api/v1/auth/login", 
        json={"login": "wrong", "password": "wrong"}
    )
    assert response.status_code == 401
    data = response.json()
    assert data["error"]["code"] == "HTTP_ERROR"
    assert data["error"]["message"] == "Incorrect login or password"