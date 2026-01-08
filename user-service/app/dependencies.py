import uuid
from typing import Optional, Annotated

from app.security import decode_token
from app.settings import Settings, get_settings
from app.schemas import TokenData

from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


def get_token(
    token: Annotated[Optional[str], Depends(oauth2_scheme)]
):
    return token


def get_current_user_data(
    token: Annotated[Optional[str], Depends(get_token)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> TokenData:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
    )
    if token is None:
        raise credentials_exception

    payload = decode_token(token, settings.secret_key)
    print(payload)
    if payload is None:
        raise credentials_exception

    try:
        return TokenData.model_validate(payload)
    except ValueError:
        raise credentials_exception
    

def get_current_user_id(current_user_data: Annotated[TokenData, Depends(get_current_user_data)]) -> Optional[uuid.UUID]:
    return current_user_data.sub


def require_permission(required_perms: list[str]):
    async def permission_checker(
        current_user_data: Annotated[TokenData, Depends(get_current_user_data)]
    ):
        if not all([perm in current_user_data.scopes for perm in required_perms]):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Not enough permissions."
            )
        return True
    
    return permission_checker
