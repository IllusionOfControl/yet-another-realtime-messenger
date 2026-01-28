from typing import Annotated, Optional

from fastapi import Depends, status
from fastapi.security import OAuth2PasswordBearer

from app.database import get_redis_client
from app.schemas import TokenData
from app.security import decode_token
from app.settings import Settings, get_settings
from app.exceptions import AppException
from redis import Redis

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


async def get_current_user_data(
    token: Annotated[Optional[str], Depends(oauth2_scheme)],
    settings: Annotated[Settings, Depends(get_settings)],
    redis_client: Annotated[Redis, Depends(get_redis_client)],
) -> TokenData:
    credentials_exception = AppException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        message="Could not validate credentials",
    )
    if token is None:
        raise credentials_exception

    payload = decode_token(token, settings.public_key)
    if payload is None:
        raise credentials_exception

    jti = payload.get("jti")
    if jti:
        is_blacklisted = await redis_client.exists(f"blacklist:{jti}")
        if is_blacklisted:
            raise AppException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                message="Token has been revoked",
            )

    try:
        return TokenData.model_validate(payload)
    except ValueError:
        raise credentials_exception
