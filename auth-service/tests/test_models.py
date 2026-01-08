import uuid
from datetime import datetime, timezone
from app.models import (
    User, 
    UserLocalAuth, 
    UserExternalAuth, 
    UserRole, 
    UserSession, 
    UserRoleEnum, 
    AuthProviderEnum
)

def test_user_model():
    user_id = uuid.uuid4()
    user = User(
        id=user_id,  
        is_active=True
    )
    assert user.id == user_id
    assert user.is_active is True
    assert user.created_at is None


def test_user_local_auth_model():
    user_id = uuid.uuid4()
    local_auth = UserLocalAuth(
        user_id=user_id,
        email="test@example.com",
        username="test_username",
        password_hash="super_secret_hash",
    )
    assert local_auth.user_id == user_id
    assert local_auth.email == "test@example.com"
    assert local_auth.password_hash == "super_secret_hash"
    assert local_auth.username == "test_username"


def test_user_external_auth_model():
    user_id = uuid.uuid4()
    external_auth = UserExternalAuth(
        user_id=user_id,
        provider=AuthProviderEnum.GOOGLE,
        provider_user_id="google-unique-subject-id",
        provider_email="google_user@gmail.com"
    )
    assert external_auth.user_id == user_id
    assert external_auth.provider == AuthProviderEnum.GOOGLE
    assert external_auth.provider_user_id == "google-unique-subject-id"
    assert external_auth.provider_email == "google_user@gmail.com"


def test_user_role_model():
    user_id = uuid.uuid4()
    role_enum = UserRoleEnum.ADMIN
    user_role = UserRole(
        user_id=user_id, 
        role=role_enum
    )
    assert user_role.user_id == user_id
    assert user_role.role == role_enum


def test_user_session_model():
    user_id = uuid.uuid4()
    access_token_jti = uuid.uuid4()
    refresh_token_jti = uuid.uuid4()
    expiry = datetime.now(timezone.utc)
    
    session = UserSession(
        user_id=user_id,
        access_token_jti=access_token_jti,
        refresh_token_jti=refresh_token_jti,
        expires_at=expiry,
        user_agent="Mozilla/5.0",
        ip_address="192.168.1.1",
        is_active=True
    )
    
    assert session.user_id == user_id
    assert session.access_token_jti == access_token_jti
    assert session.refresh_token_jti == refresh_token_jti
    assert session.expires_at == expiry
    assert session.user_agent == "Mozilla/5.0"
    assert session.ip_address == "192.168.1.1"
    assert session.is_active is True