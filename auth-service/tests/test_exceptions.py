import pytest
from unittest.mock import AsyncMock, Mock
import httpx
from fastapi import FastAPI
from app.database import get_db

@pytest.mark.asyncio
async def test_standardized_404_error(client: httpx.AsyncClient):
    response = await client.get("/api/v1/auth/non-existent-endpoint")
    assert response.status_code == 404
    
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "HTTP_ERROR"
    assert "message" in data["error"]
    assert "trace_id" in data["error"]
    assert data["error"]["trace_id"] is not None

@pytest.mark.asyncio
async def test_standardized_validation_error(client: httpx.AsyncClient):
    """Test that Pydantic validation errors return the standard error format."""
    response = await client.post("/api/v1/auth/register", json={})
    assert response.status_code == 422
    
    data = response.json()
    assert data["error"]["code"] == "VALIDATION_ERROR"
    assert "details" in data["error"]
    assert isinstance(data["error"]["details"], list)
    assert data["error"]["trace_id"] is not None

@pytest.mark.asyncio
async def test_standardized_500_error(app: FastAPI, client: httpx.AsyncClient):
    async def mock_side_effect(*args, **kwargs):
        raise Exception("Database Crash!")
    
    mock_get_db_crash = Mock()
    mock_get_db_crash.execute = AsyncMock(side_effect=mock_side_effect)
    
    app.dependency_overrides[get_db] = lambda: mock_get_db_crash
    response = await client.post(
        "/api/v1/auth/login", 
        json={"login": "test", "password": "password"}
    )
        
    assert response.status_code == 500
    data = response.json()
    assert data["error"]["code"] == "INTERNAL_SERVER_ERROR"
    assert data["error"]["message"] == "An unexpected error occurred"
    assert "Database crash!" not in data["error"]["message"]
    assert data["error"]["trace_id"] is not None

@pytest.mark.asyncio
async def test_app_exception_handling(client: httpx.AsyncClient):
    response = await client.post(
        "/api/v1/auth/login", 
        json={"login": "wrong", "password": "wrong"}
    )
    assert response.status_code == 401
    data = response.json()
    assert data["error"]["code"] == "BAD_REQUEST"
    assert data["error"]["message"] == "Incorrect login or password"