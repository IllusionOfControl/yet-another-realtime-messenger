import os
import uuid
from datetime import datetime
from typing import AsyncGenerator, AsyncIterator
from unittest.mock import AsyncMock, Mock

import httpx
import pytest
from fastapi import FastAPI
from redis.asyncio import Redis, from_url
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

from app.database import Base, get_db, get_redis_client
from app.main import get_app
from app.services.user_client import UserClient, UserProfile, get_user_client
from app.settings import get_settings


@pytest.fixture(scope="session")
def test_rsa_keys() -> tuple[str, str]:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = private_key.public_key()
    
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    ).decode("utf-8")
    
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode("utf-8")
    
    return (private_pem, public_pem)


@pytest.fixture(scope="session", autouse=True)
def update_environment(test_rsa_keys: tuple[str, str]):
    private_pem, public_pem = test_rsa_keys
    os.environ["PRIVATE_KEY"] = private_pem
    os.environ["PUBLIC_KEY"] = public_pem
    yield


@pytest.fixture()
async def app(update_environment) -> AsyncIterator[FastAPI]:
    yield get_app()


@pytest.fixture()
async def db_session() -> AsyncGenerator[AsyncSession, None]:
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
async def client(app: FastAPI) -> AsyncGenerator[httpx.AsyncClient, None]:
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client


@pytest.fixture
def mock_user_service_client() -> UserClient:
    mock_client = Mock(spec=UserClient)

    mock_client.create_user_profile = AsyncMock(
        side_effect=lambda *args, **kwargs: UserProfile(
            id=uuid.uuid4(),
            email=kwargs["email"],
            username=kwargs["username"],
            display_name=kwargs["display_name"],
            created_at=datetime.now(),
            updated_at=datetime.now(),
            is_active=True,
            roles=["user"],
        ),
    )
    mock_client.get_user_by_id = AsyncMock(
        side_effect=lambda *args, **kwargs: UserProfile(
            id=kwargs["user_id"],
            email="email@email.com",
            username="username",
            display_name="username",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            is_active=True,
            roles=["user"],
        ),
    )
    return mock_client



@pytest.fixture
async def mock_redis_client() -> AsyncGenerator[Redis, None]:
    settings = get_settings()
    redis = from_url(settings.redis_url, decode_responses=True)
    await redis.flushdb()

    yield redis

    await redis.flushdb()
    await redis.aclose()


@pytest.fixture(autouse=True)
def override_fastapi_depends(
    app: FastAPI, 
    db_session: AsyncSession, 
    mock_user_service_client: UserClient, 
    mock_redis_client: Redis
):
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_user_client] = lambda: mock_user_service_client
    app.dependency_overrides[get_redis_client] = lambda: mock_redis_client

    yield

    app.dependency_overrides.clear()


