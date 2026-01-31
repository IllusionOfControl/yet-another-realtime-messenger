from typing import Any, Optional

import jwt


def decode_token(token: str, public_key: str) -> Optional[dict[str, Any]]:
    try:
        payload = jwt.decode(token, public_key, algorithms=["RS256"])
        return payload
    except (jwt.DecodeError, jwt.ExpiredSignatureError, jwt.InvalidAlgorithmError):
        return None
