import uuid
from typing import Optional

from fastapi import Header, HTTPException, status


async def get_current_user_id(x_user_id: Optional[str] = Header(None)) -> uuid.UUID:
    if x_user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="X-User-Id header missing"
        )
    try:
        user_id = uuid.UUID(x_user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid X-User-Id format"
        )
    return user_id
