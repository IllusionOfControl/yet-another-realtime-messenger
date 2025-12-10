import uuid
from typing import AsyncGenerator, AsyncIterator
from unittest.mock import AsyncMock, patch

import httpx
import pytest
import pytest_asyncio
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.database import Base, get_db
from app.main import get_app


@pytest.fixture
async def app() -> AsyncIterator[FastAPI]:
    yield get_app()


@pytest.fixture(autouse=True)
async def db_session(app) -> AsyncGenerator[AsyncSession, None]:
    """Test database session for each test."""
    engine = create_async_engine(settings.database_url, echo=False)

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)

    async with engine.begin() as connection:
        await connection.begin_nested()
        session = AsyncSession(bind=connection, expire_on_commit=False)

        app.dependency_overrides[get_db] = lambda: session

        yield session

    app.dependency_overrides.clear()


@pytest.fixture
async def client(app) -> AsyncGenerator[TestClient, None]:
    """Test HTTP client for FastAPI."""
    # return TestClient(app)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as c:
        yield c


@pytest.fixture
def mock_file_upload_client():
    """Mock the FileUploadClient for testing external service calls."""
    with patch(
        "app.services.file_upload_client.file_upload_client", autospec=True
    ) as mock_client:
        mock_client.get_signed_url = AsyncMock(
            return_value="http://mock.signed.url/avatar.jpg"
        )
        mock_client.upload_file = AsyncMock(
            return_value={
                "id": str(uuid.uuid4()),
                "url": "http://mock.cdn/uploaded.jpg",
            }
        )
        yield mock_client
