import enum
import uuid

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class ContactStatus(enum.Enum):
    FRIEND = "FRIEND"
    BLOCKED = "BLOCKED"


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String, unique=True, index=True, nullable=False)
    display_name = Column(String, nullable=True)
    email = Column(String, unique=True, index=True, nullable=True)
    bio = Column(String, nullable=True)
    avatar_file_id = Column(UUID(as_uuid=True), nullable=True)
    custom_status = Column(String, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    is_active = Column(Boolean, default=True, nullable=False)

    owned_contacts = relationship(
        "UserContact",
        foreign_keys="UserContact.owner_id",
        back_populates="owner",
        lazy="selectin",
        cascade="all, delete-orphan",
    )
    related_contacts = relationship(
        "UserContact",
        foreign_keys="UserContact.contact_user_id",
        back_populates="contact",
        lazy="selectin",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<UserProfile(id='{self.id}', username='{self.username}')>"


class UserContact(Base):
    __tablename__ = "user_contacts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id = Column(
        UUID(as_uuid=True), ForeignKey("user_profiles.id"), nullable=False
    )
    contact_user_id = Column(
        UUID(as_uuid=True), ForeignKey("user_profiles.id"), nullable=False
    )
    status = Column(Enum(ContactStatus), nullable=False)
    created_at = Column(DateTime, default=func.now())

    __table_args__ = (
        UniqueConstraint("owner_id", "contact_user_id", name="_owner_contact_uc"),
    )

    owner = relationship(
        "UserProfile", foreign_keys=[owner_id], back_populates="owned_contacts"
    )
    contact = relationship(
        "UserProfile", foreign_keys=[contact_user_id], back_populates="related_contacts"
    )

    def __repr__(self):
        return f"<UserContact(owner_id='{self.owner_id}', contact_user_id='{self.contact_user_id}', status='{self.status.name}')>"
