import os
import uuid
from typing import AsyncGenerator, AsyncIterator
from unittest.mock import AsyncMock, Mock

import httpx
import pytest
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from redis.asyncio import Redis

from app.database import Base, get_db, get_redis_client
from app.main import get_app
from app.dependencies import get_current_user_data
from app.schemas import TokenData
from app.services.kafka_producer import KafkaProducerService, get_kafka_producer
from app.settings import get_settings
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from datetime import datetime, timezone, timedelta
import jwt

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


@pytest.fixture(scope="function")
def jwt_token_factory(test_rsa_keys: tuple[str, str]):
    private_key, public_key = test_rsa_keys
    settings = get_settings()
    
    def _jwt_token_factory(private_key: str = private_key, **kwargs):
        payload = {
            "sub": str(kwargs.get("sub", uuid.uuid4())),
            "scopes": kwargs.get("scopes", []),
            "sid": str(kwargs.get("sid", uuid.uuid4())),
            "jti": str(kwargs.get("jti", uuid.uuid4())),
            "exp": kwargs.get("exp", datetime.now(timezone.utc) + timedelta(minutes=15)), 
            "iat": kwargs.get("iat", datetime.now(timezone.utc)),
        }
        return jwt.encode(payload, private_key, algorithm="RS256")
    
    return _jwt_token_factory


@pytest.fixture()
async def app() -> AsyncIterator[FastAPI]:
    yield get_app()

@pytest.fixture()
async def db_session(app: FastAPI) -> AsyncGenerator[AsyncSession, None]:
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
def mock_kafka_producer() -> KafkaProducerService:
    mock_service = Mock(spec=KafkaProducerService)
    mock_service.publish_event = AsyncMock()
    mock_service.start = AsyncMock()
    mock_service.stop = AsyncMock()
    return mock_service

@pytest.fixture
def mock_redis_client() -> Redis:
    mock_redis = Mock(spec=Redis)
    mock_redis.exists = AsyncMock(return_value=False)
    return mock_redis

@pytest.fixture
def current_user_id() -> uuid.UUID:
    return uuid.uuid4()

@pytest.fixture(autouse=True)
def override_dependencies(
    app: FastAPI,
    db_session: AsyncSession,
    mock_kafka_producer: KafkaProducerService,
    mock_redis_client: Redis,
    current_user_id: uuid.UUID,
):
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_kafka_producer] = lambda: mock_kafka_producer
    app.dependency_overrides[get_redis_client] = lambda: mock_redis_client
    app.dependency_overrides[get_current_user_data] = lambda: TokenData(
        sub=current_user_id,
        scopes=["chat.message.send", "chat.group.create", "chat.channel.create"],
        sid=uuid.uuid4(),
        jti=uuid.uuid4()
    )

    yield

    app.dependency_overrides.clear()
