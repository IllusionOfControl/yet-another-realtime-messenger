import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, HttpUrl

from app.models import ContactStatus


class ErrorDetail(BaseModel):
    message: str
    code: str
    trace_id: Optional[str] = None
    details: Optional[str | list | dict] = None

class ErrorResponse(BaseModel):
    error: ErrorDetail


class UserProfileCreate(BaseModel):
    username: str = Field(min_length=3, max_length=32)
    display_name: Optional[str] = None
    email: EmailStr


class UserProfileUpdate(BaseModel):
    display_name: Optional[str] = None
    email: Optional[EmailStr] = None
    bio: Optional[str] = None
    custom_status: Optional[str] = None


class UserProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    username: str = Field(min_length=3, max_length=32)
    display_name: Optional[str] = None
    email: Optional[EmailStr] = None
    bio: Optional[str] = None
    custom_status: Optional[str] = None
    avatar_url: Optional[HttpUrl] = None
    created_at: datetime
    updated_at: datetime


class UserSearchResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    username: str
    display_name: Optional[str] = None
    avatar_url: Optional[HttpUrl] = None


class ContactResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)
    id: uuid.UUID
    contact_id: uuid.UUID
    status: ContactStatus
    username: str
    display_name: Optional[str] = None
    avatar_url: Optional[HttpUrl] = None


class SearchParams(BaseModel):
    query: str = Field(min_length=1)
    limit: int = Field(10, gt=0, le=100)
    offset: int = Field(0, ge=0)


class TokenData(BaseModel):
    sub: uuid.UUID
    scopes: list[str]
    sid: uuid.UUID
    jti: uuid.UUID