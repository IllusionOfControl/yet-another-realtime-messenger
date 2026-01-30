import uuid
from typing import Optional, Annotated

from app.security import decode_token
from app.settings import Settings, get_settings
from app.schemas import TokenData

from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from redis.asyncio import Redis
from app.database import get_redis_client

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


def get_token(
    token: Annotated[Optional[str], Depends(oauth2_scheme)]
):
    return token


async def get_current_user_data(
    token: Annotated[Optional[str], Depends(get_token)],
    settings: Annotated[Settings, Depends(get_settings)],
    redis_client: Annotated[Redis, Depends(get_redis_client)],
) -> TokenData:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
    )
    if token is None:
        raise credentials_exception

    payload = decode_token(token, settings.secret_key)
    if payload is None:
        raise credentials_exception
    
    jti = payload.get("jti")
    if jti:
        is_blacklisted = await redis_client.exists(f"blacklist:{jti}")
        if is_blacklisted:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked",
            )

    try:
        return TokenData.model_validate(payload)
    except Exception:
        raise credentials_exception
    

def get_current_user_id(current_user_data: Annotated[TokenData, Depends(get_current_user_data)]) -> Optional[uuid.UUID]:
    return current_user_data.sub
