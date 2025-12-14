import logging
import uuid
from datetime import datetime
from functools import lru_cache
from http import HTTPStatus
from typing import Optional

import httpx
from pydantic import BaseModel

from app.settings import get_settings

logger = logging.getLogger(__name__)


class UserClientError(Exception):
    def __init__(
        self,
        detail: Optional[str],
        status_code: int = HTTPStatus.INTERNAL_SERVER_ERROR.value,
    ):
        super().__init__(detail)
        self.detail = detail
        self.status_code = status_code


class UserProfile(BaseModel):
    id: uuid.UUID
    username: str
    display_name: Optional[str] = None
    email: Optional[str] = None
    bio: Optional[str] = None
    custom_status: Optional[str] = None
    avatar_url: Optional[str] = None
    is_active: bool
    roles: list[str]
    created_at: datetime
    updated_at: datetime


class UserClient:
    def __init__(self, base_url: str):
        self.client = httpx.AsyncClient(base_url=base_url)

    async def create_user_profile(
        self, *, username: str, email: str, display_name: Optional[str] = None
    ) -> UserProfile:
        try:
            payload = {
                "username": username,
                "display_name": display_name,
                "email": email,
            }
            response = await self.client.post(
                "/api/v1/users/internal/create-profile", json=payload, timeout=5
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            if e.response.status_code != HTTPStatus.INTERNAL_SERVER_ERROR.value:
                error_detail = e.response.json().get("detail", "Unknown error")
            else:
                error_detail = "Internal server error"

            logger.error(
                f"Error creating user profile in User Service: {e.response.status_code} - {e.response.text}"
            )
            raise UserClientError(
                detail=error_detail, status_code=e.response.status_code
            )
        except httpx.RequestError as e:
            logger.error(f"Request error creating user profile in User Service: {e}")
            error_detail = f"User Service unreachable: {e}"
            raise UserClientError(
                detail=error_detail, status_code=HTTPStatus.SERVICE_UNAVAILABLE.value
            )
        return UserProfile.model_validate_json(response.text)

    async def get_user_by_id(self, *, user_id: uuid.UUID) -> UserProfile:
        try:
            response = await self.client.get(f"/api/v1/users/{str(user_id)}", timeout=5)
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR.value:
                error_detail = "Internal server error"
            else:
                error_detail = e.response.json().get("detail", "Unknown error")

            logger.error(
                f"Error creating user profile in User Service: {e.response.status_code} - {e.response.text}"
            )
            raise UserClientError(
                detail=error_detail, status_code=e.response.status_code
            )
        except httpx.RequestError as e:
            logger.error(f"Request error creating user profile in User Service: {e}")
            error_detail = f"User Service unreachable: {e}"
            raise UserClientError(
                detail=error_detail, status_code=HTTPStatus.SERVICE_UNAVAILABLE.value
            )
        return UserProfile.model_validate_json(response.text)


@lru_cache
def get_user_client():
    settings = get_settings()
    return UserClient(settings.user_service_url)
