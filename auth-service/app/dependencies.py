from typing import Annotated, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.database import get_redis_client
from app.schemas import TokenData
from app.security import decode_token
from app.settings import Settings, get_settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


async def get_current_user_data(
    token: Annotated[Optional[str], Depends(oauth2_scheme)],
    settings: Annotated[Settings, Depends(get_settings)],
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

    # TODO: Проверить Acess Token в чёрном списке

    print("payload>", payload)

    try:
        return TokenData.model_validate(payload)
    except ValueError:
        raise credentials_exception
