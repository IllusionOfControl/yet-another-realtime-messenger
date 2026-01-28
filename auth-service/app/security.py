from datetime import datetime
from typing import Any, Optional

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

ph = PasswordHasher()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return ph.verify(hashed_password, plain_password)
    except VerifyMismatchError as e:
        return False


def get_password_hash(password: str) -> str:
    return ph.hash(password)


def create_jwt_token(
    data: dict[str, Any], private_key: str, issued_at: datetime, expires_at: datetime
) -> str:
    to_encode = data.copy()
    to_encode.update({"exp": expires_at, "iat": issued_at})
    encoded_jwt = jwt.encode(to_encode, private_key, algorithm="RS256")
    return encoded_jwt


def decode_token(token: str, public_key: str) -> Optional[dict[str, Any]]:
    try:
        payload = jwt.decode(token, public_key, algorithms=["RS256"])
        return payload
    except (jwt.DecodeError, jwt.ExpiredSignatureError):
        return None
