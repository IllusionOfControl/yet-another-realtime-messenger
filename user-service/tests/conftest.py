import uuid
from typing import AsyncGenerator, AsyncIterator
from unittest.mock import AsyncMock, Mock

import httpx
import pytest
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.database import Base, get_db
from app.main import get_app
from app.services.file_upload_client import FileUploadClient, get_file_upload_client
from app.settings import get_settings
from app.models import UserProfile, UserContact, ContactStatus
import random

from faker import Faker
from datetime import datetime, timezone

fake = Faker()


@pytest.fixture
async def app() -> AsyncIterator[FastAPI]:
    yield get_app()


@pytest.fixture()
async def db_session(app) -> AsyncGenerator[AsyncSession, None]:
    settings = get_settings()
    engine = create_async_engine(settings.database_url, echo=False)

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)

    async with engine.begin() as connection:
        await connection.begin_nested()
        session = AsyncSession(bind=connection, expire_on_commit=False)
        yield session


@pytest.fixture
async def client(app) -> AsyncGenerator[httpx.AsyncClient, None]:
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client


@pytest.fixture()
def mock_file_upload_client():
    mock_client = Mock(spec=FileUploadClient)
    mock_client.get_signed_url = AsyncMock(
        return_value="http://mock_file_upload_service/avatar.jpg"
    )
    mock_client.upload_file = AsyncMock(
        return_value={
            "id": str(uuid.uuid4()),
            "url": "http://mock_file_upload_service/uploaded.jpg",
            "size_bytes": 12345,
            "mime_type": "image/png",
        }
    )
    yield mock_client


@pytest.fixture(autouse=True)
def override_fastapi_depends(app, db_session, mock_file_upload_client):
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_file_upload_client] = lambda: mock_file_upload_client

    yield

    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def user_profile_factory():
    def _user_profile_factory(**kwargs):
        return UserProfile(
            id=kwargs.get("id", uuid.uuid4()),
            username=kwargs.get("username", fake.user_name()),
            display_name=kwargs.get("display_name", fake.name()),
            email=kwargs.get("email", fake.email()),
            bio=kwargs.get("bio", fake.sentence()),
            avatar_file_id=kwargs.get("avatar_file_id", fake.uuid4() if random.choice([True, False]) else None),
            custom_status=kwargs.get("custom_status", fake.word() if random.choice([True, False]) else None),
            created_at=kwargs.get("created_at", datetime.now(timezone.utc)),
            updated_at=kwargs.get("updated_at", datetime.now(timezone.utc)),
        )
    return _user_profile_factory


@pytest.fixture(scope="function")
def user_contact_factory():
    def _user_contact_factory(owner_id: uuid.UUID, contact_id: uuid.UUID, **kwargs):
        return UserContact(
            id=kwargs.get("id", uuid.uuid4()),
            owner_id=owner_id,
            contact_id=contact_id,
            status=kwargs.get("status", random.choice(list(ContactStatus))),
            created_at=kwargs.get("created_at", datetime.now(timezone.utc)),
        )
    return _user_contact_factory