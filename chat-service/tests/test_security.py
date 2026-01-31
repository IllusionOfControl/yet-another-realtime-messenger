import uuid
from datetime import datetime, timedelta, timezone
import jwt
from cryptography.hazmat.primitives.asymmetric import rsa 
from cryptography.hazmat.primitives import serialization

from app.security import (
    decode_token,
)


def test_decode_rs256_access_token(test_rsa_keys: tuple[str, str]):
    private_key, public_key = test_rsa_keys
    user_id = uuid.uuid4()
    scopes = ["user.profile.view"]
    issued_at = datetime.now(timezone.utc)
    expires_at = issued_at + timedelta(minutes=15)
    
    payload = {
        "sub": str(user_id), 
        "scopes": scopes, 
        "exp": expires_at, 
        "iat": issued_at,
        "jti": str(uuid.uuid4())
    }
    
    encoded_jwt = jwt.encode(payload, private_key, algorithm="RS256")
    
    decoded = decode_token(encoded_jwt, public_key)
    
    assert decoded is not None
    assert decoded["sub"] == str(user_id)
    assert decoded["scopes"] == scopes
    assert "exp" in decoded

def test_rs256_rejection_with_wrong_key(test_rsa_keys: tuple[str, str]):
    private_pem, _ = test_rsa_keys
    other_priv = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    other_pub_pem = other_priv.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode("utf-8")
    
    payload = {"sub": "attacker"}
    token = jwt.encode(payload, "secret", algorithm="HS256")
    
    payload = decode_token(token, other_pub_pem)
    assert payload is None