import uuid
from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models import ChatType, MemberRole


class ChatMemberSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    user_id: uuid.UUID
    role: MemberRole
    joined_at: datetime


class GroupCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class ChannelCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    is_public: bool = True


class ChatUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_public: Optional[bool] = None


class ParticipantAdd(BaseModel):
    user_id: uuid.UUID


class RoleUpdate(BaseModel):
    role: MemberRole


class ChatResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    type: ChatType
    name: Optional[str]
    settings: dict
    created_at: datetime
    members: List[ChatMemberSchema]


class ChatShortResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    type: ChatType
    name: Optional[str]
    created_at: datetime


class MembershipCheckResponse(BaseModel):
    is_member: bool
    role: Optional[MemberRole] = None


class TokenData(BaseModel):
    sub: uuid.UUID
    scopes: List[str] = []
    sid: Optional[uuid.UUID] = None
    jti: Optional[uuid.UUID] = None
