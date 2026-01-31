import enum
import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import JSON, Enum, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ChatType(enum.Enum):
    DM = "DM"
    GROUP = "GROUP"
    CHANNEL = "CHANNEL"


class MemberRole(enum.Enum):
    OWNER = "OWNER"
    ADMIN = "ADMIN"
    MEMBER = "MEMBER"


class Chat(Base):
    __tablename__ = "chats"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    type: Mapped[ChatType] = mapped_column(Enum(ChatType), nullable=False)
    name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    settings: Mapped[dict] = mapped_column(JSON, default={}, nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        default=func.now(), onupdate=func.now(), nullable=False
    )

    members: Mapped[List["ChatMember"]] = relationship(
        "ChatMember",
        back_populates="chat",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self):
        return f"<Chat(id='{self.id}', type='{self.type.name}', name='{self.name}')>"


class ChatMember(Base):
    __tablename__ = "chat_members"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    chat_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("chats.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(nullable=False, index=True)
    role: Mapped[MemberRole] = mapped_column(
        Enum(MemberRole), default=MemberRole.MEMBER, nullable=False
    )
    joined_at: Mapped[datetime] = mapped_column(default=func.now(), nullable=False)

    chat: Mapped["Chat"] = relationship("Chat", back_populates="members")

    def __repr__(self):
        return f"<ChatMember(chat_id='{self.chat_id}', user_id='{self.user_id}', role='{self.role.name}')>"
