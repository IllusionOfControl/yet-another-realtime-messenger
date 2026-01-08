from typing import Any, Optional

import jwt


def decode_token(token: str, secret_key: str) -> Optional[dict[str, Any]]:
    try:
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
        return payload
    except jwt.DecodeError:
        return None
    except jwt.ExpiredSignatureError:
        return None
