import uuid
from datetime import datetime
from enum import StrEnum
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class UserRoleEnum(StrEnum):
    USER = "user"
    ADMIN = "admin"


class AuthProviderEnum(StrEnum):
    LOCAL = "local"
    GOOGLE = "google"
    GITHUB = "github"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(default=func.now())

    local_auth: Mapped[Optional["UserLocalAuth"]] = relationship(
        back_populates="user", lazy="joined"
    )
    external_auths: Mapped[list["UserExternalAuth"]] = relationship(
        back_populates="user", lazy="selectin"
    )
    sessions: Mapped[list["UserSession"]] = relationship(
        back_populates="user", lazy="selectin"
    )
    roles: Mapped[list["UserRole"]] = relationship(
        back_populates="user", lazy="selectin"
    )

    def __repr__(self):
        return f"<User(id='{self.id}')>"


class UserLocalAuth(Base):
    __tablename__ = "user_local_auth"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), primary_key=True)
    username: Mapped[str] = mapped_column(
        String(32), unique=True, index=True, nullable=False
    )
    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    password_updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), onupdate=func.now()
    )
    email_updated_at: Mapped[datetime] = mapped_column(
        default=func.now(), onupdate=func.now()
    )

    email_verified_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    verification_code: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)

    user: Mapped["User"] = relationship(back_populates="local_auth")

    def __repr__(self):
        return f"<UserLocalAuth(user_id='{self.user_id}')>"


class UserExternalAuth(Base):
    __tablename__ = "user_external_auth"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )

    provider: Mapped[AuthProviderEnum] = mapped_column(nullable=False)
    provider_user_id: Mapped[str] = mapped_column(
        String(255), nullable=False, index=True
    )

    provider_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    created_at: Mapped[datetime] = mapped_column(default=func.now())

    user: Mapped["User"] = relationship(back_populates="external_auths", lazy="joined")

    __table_args__ = (
        UniqueConstraint("provider", "provider_user_id", name="_provider_user_uc"),
    )

    def __repr__(self):
        return f"<UserExternalAuth(id='{self.id}', user_id='{self.user_id}, provider='{self.provider}')>"


class UserRole(Base):
    __tablename__ = "user_roles"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )
    role: Mapped[UserRoleEnum] = mapped_column(nullable=False)

    user: Mapped[User] = relationship("User", back_populates="roles")

    def __repr__(self):
        return f"<UserRole(id='{self.id}', user_id='{self.user_id}', role='{self.role}', role={self.role})>"


class UserSession(Base):
    __tablename__ = "user_sessions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )
    access_token_jti: Mapped[uuid.UUID] = mapped_column(unique=True, nullable=False)
    refresh_token_jti: Mapped[uuid.UUID] = mapped_column(unique=True, nullable=False)
    issued_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    user_agent: Mapped[Optional[str]] = mapped_column(nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    user: Mapped[User] = relationship("User", back_populates="sessions")

    def __repr__(self):
        return f"<UserSession(id='{self.id}', user_id='{self.user_id}', is_active={self.is_active})>"
