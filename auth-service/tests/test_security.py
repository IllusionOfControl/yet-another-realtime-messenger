import uuid
from datetime import datetime, timedelta, timezone
from cryptography.hazmat.primitives import rsa, serialization
import jwt

from app.security import (
    create_jwt_token,
    decode_token,
    get_password_hash,
    verify_password,
)


def test_password_hashing():
    password = "MySecurePassword123"
    hashed_password = get_password_hash(password)
    assert verify_password(password, hashed_password)
    assert not verify_password("wrongpassword", hashed_password)


def test_rs256_token_signing_and_decoding(test_rsa_keys: tuple[str, str]):
    private_pem, public_pem = test_rsa_keys
    user_id = uuid.uuid4()
    scopes = ["example_scope"]
    issued_at = datetime.now(timezone.utc)
    expires_at = issued_at + timedelta(minutes=1)

    token = create_jwt_token(
        {"sub": str(user_id), "scopes": scopes},
        private_key=private_pem,
        issued_at=issued_at,
        expires_at=expires_at,
    )

    header = jwt.get_unverified_header(token)
    assert header["alg"] == "RS256"

    payload = decode_token(token, public_pem)
    assert payload is not None
    assert payload["sub"] == str(user_id)
    assert payload["scopes"] == scopes
    assert "exp" in payload
    assert "iat" in payload
    assert "sub" in payload

def test_rs256_rejection_with_wrong_key(test_rsa_keys: tuple[str, str]):
    private_pem, public_pem = test_rsa_keys
    other_priv = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    other_pub_pem = other_priv.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode("utf-8")
    
    token = create_jwt_token(
        {"sub": "test"},
        private_key=test_rsa_keys["private"],
        issued_at=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=1),
    )
    
    payload = decode_token(token, other_pub_pem)
    assert payload is None