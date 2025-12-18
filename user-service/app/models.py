import enum
import uuid

from sqlalchemy import (
    Enum,
    ForeignKey,
    UniqueConstraint,
    func,
    String,
)
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.database import Base
from datetime import datetime

class ContactStatus(enum.Enum):
    FRIEND = "FRIEND"
    BLOCKED = "BLOCKED"


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    username: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    display_name: Mapped[str] = mapped_column(nullable=True)
    email: Mapped[str] = mapped_column(unique=True, index=True, nullable=False)
    bio: Mapped[str] = mapped_column(nullable=True)
    avatar_file_id: Mapped[uuid.UUID] = mapped_column(nullable=True)
    custom_status: Mapped[str] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(default=func.now(), onupdate=func.now(), nullable=False)

    owned_contacts = relationship(
        "UserContact",
        foreign_keys="UserContact.owner_id",
        back_populates="owner",
        lazy="selectin",
        cascade="all, delete-orphan",
    )
    related_contacts = relationship(
        "UserContact",
        foreign_keys="UserContact.contact_id",
        back_populates="contact",
        lazy="selectin",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<UserProfile(id='{self.id}', username='{self.username}')>"


class UserContact(Base):
    __tablename__ = "user_contacts"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    owner_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("user_profiles.id"), nullable=False)
    contact_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("user_profiles.id"), nullable=False)
    status: Mapped[ContactStatus] = mapped_column(Enum(ContactStatus), nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=func.now())

    __table_args__ = (
        UniqueConstraint("owner_id", "contact_id", name="_owner_contact_uc"),
    )

    owner = relationship(
        "UserProfile", foreign_keys=[owner_id], back_populates="owned_contacts"
    )
    contact = relationship(
        "UserProfile", foreign_keys=[contact_id], back_populates="related_contacts"
    )

    def __repr__(self):
        return f"<UserContact(owner_id='{self.owner_id}', contact_id='{self.contact_id}', status='{self.status.name}')>"
