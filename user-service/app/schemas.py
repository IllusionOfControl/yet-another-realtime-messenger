import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, HttpUrl

from app.models import ContactStatus


class UserProfileBase(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    display_name: Optional[str] = None
    email: Optional[EmailStr] = None
    bio: Optional[str] = None
    custom_status: Optional[str] = None


class UserProfileCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    display_name: Optional[str] = None
    email: Optional[EmailStr] = None


class UserProfileUpdate(BaseModel):
    display_name: Optional[str] = None
    email: Optional[EmailStr] = None
    bio: Optional[str] = None
    custom_status: Optional[str] = None


class UserProfileResponse(UserProfileBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
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
    contact_user_id: uuid.UUID
    status: ContactStatus
    username: str
    display_name: Optional[str] = None
    avatar_url: Optional[HttpUrl] = None


class SearchParams(BaseModel):
    query: str = Field(min_length=1)
    limit: int = Field(10, gt=0, le=100)
    offset: int = Field(0, ge=0)