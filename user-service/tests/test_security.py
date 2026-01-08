import uuid
from datetime import datetime, timedelta, timezone
import jwt

from app.security import (
    decode_token,
)


def test_decode_access_token():
    user_id = uuid.uuid4()
    scopes = ["example_scope"]
    secret_key = "secret_key"
    issued_at = datetime.now(timezone.utc)
    expires_at = issued_at + timedelta(minutes=1)

    payload = ({
        "sub": str(user_id), 
        "scopes": scopes, 
        "exp": expires_at, 
        "iat": issued_at
    })
    encoded_jwt = jwt.encode(payload, secret_key, algorithm="HS256")

    payload = decode_token(encoded_jwt, secret_key)
    assert payload is not None
    assert payload["sub"] == str(user_id)
    assert payload["scopes"] == scopes
    assert "exp" in payload
    assert "iat" in payload
    assert "sub" in payload