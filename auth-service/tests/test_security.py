import uuid
from datetime import timedelta, datetime, timezone

from app.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    verify_password,
)


def test_password_hashing():
    password = "MySecurePassword123"
    hashed_password = get_password_hash(password)
    assert verify_password(password, hashed_password)
    assert not verify_password("wrongpassword", hashed_password)


def test_create_and_decode_access_token():
    user_id = uuid.uuid4()
    scopes = ["example_scope"]
    secret_key = "secret_key"
    issued_at = datetime.now(timezone.utc)
    expires_at = issued_at + timedelta(minutes=1)
    token = create_access_token(
        {"sub": str(user_id), "scopes": scopes},
        secret_key=secret_key,
        issued_at=issued_at,
        expires_at=expires_at,
    )

    payload = decode_token(token, secret_key)
    assert payload is not None
    assert payload["sub"] == str(user_id)
    assert payload["scopes"] == scopes
    assert "exp" in payload
    assert "iat" in payload
    assert "sub" in payload


def test_expired_access_token():
    user_id = uuid.uuid4()
    secret_key = "secret_key"
    issued_at = datetime.now(timezone.utc)
    expires_at = issued_at - timedelta(minutes=1)
    token = create_access_token(
        {"sub": str(user_id)},
        secret_key=secret_key,
        issued_at=issued_at,
        expires_at=expires_at,
    )
    payload = decode_token(token, secret_key)
    assert payload is None


def test_create_and_decode_refresh_token():
    user_id = uuid.uuid4()
    scopes = ["example_scope"]
    secret_key = "secret_key"
    issued_at = datetime.now(timezone.utc)
    expires_at = issued_at + timedelta(minutes=1)
    token = create_refresh_token(
        {"sub": str(user_id), "scope": scopes},
        secret_key=secret_key,
        issued_at=issued_at,
        expires_at=expires_at,
    )

    payload = decode_token(token, secret_key)
    assert payload is not None
    assert payload["sub"] == str(user_id)
    assert payload["scope"] == scopes
    assert "exp" in payload
    assert "iat" in payload
    assert "sub" in payload
