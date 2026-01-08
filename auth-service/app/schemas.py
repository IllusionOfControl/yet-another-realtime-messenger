import uuid
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class SuccessResponse(BaseModel):
    message: str


class UserCreateRequest(BaseModel):
    username: str = Field(min_length=3, max_length=32)
    display_name: Optional[str] = None
    email: EmailStr
    password: str = Field(min_length=6)


class UserLoginRequest(BaseModel):
    login: str
    password: str


class TokenValidationResponse(BaseModel):
    user_id: uuid.UUID
    scopes: list[str]
    is_verified: bool


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    sub: uuid.UUID
    scopes: list[str]
    sid: uuid.UUID
    jti: uuid.UUID


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    all_devices: bool = False


class TokenValidationResponse(BaseModel):
    user_id: uuid.UUID
    scopes: list[str]
