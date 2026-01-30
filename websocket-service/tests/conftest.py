import pytest
import uuid
import jwt
import os
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from cryptography.hazmat.primitives import rsa, serialization
from fastapi.testclient import TestClient

# Mock environment before imports
os.environ["PUBLIC_KEY"] = "dummy"

from app.main import get_app, get_redis
from app.settings import get_settings

@pytest.fixture(scope="session")
def test_rsa_keys():
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
    
    return {"private": private_pem, "public": public_pem}

@pytest.fixture(autouse=True)
def mock_settings(test_rsa_keys):
    settings = get_settings()
    settings.public_key = test_rsa_keys["public"]
    settings.redis_url = "redis://localhost:6379"
    return settings

@pytest.fixture
def jwt_token_factory(test_rsa_keys):
    def _factory(user_id: str):
        payload = {
            "sub": user_id,
            "iat": datetime.now(timezone.utc),
            "exp": datetime.now(timezone.utc) + timedelta(minutes=5)
        }
        return jwt.encode(payload, test_rsa_keys["private"], algorithm="RS256")
    return _factory

@pytest.fixture
def mock_redis():
    mock = AsyncMock()
    mock.set = AsyncMock()
    mock.delete = AsyncMock()
    return mock

@pytest.fixture
def app(mock_redis):
    _app = get_app()
    _app.dependency_overrides[get_redis] = lambda: mock_redis
    yield _app
    _app.dependency_overrides.clear()

@pytest.fixture
def client(app):
    with TestClient(app) as c:
        yield c
