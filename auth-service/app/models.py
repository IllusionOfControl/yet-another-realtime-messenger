import uuid
from datetime import datetime

from sqlalchemy import func, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional

from app.database import Base
from enum import StrEnum


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
    
    local_auth: Mapped[Optional["UserLocalAuth"]] = relationship(back_populates="user")
    external_auths: Mapped[list["UserExternalAuth"]] = relationship(back_populates="user")
    sessions: Mapped[list["UserSession"]] = relationship(back_populates="user")
    roles: Mapped[list["UserRole"]] = relationship(back_populates="user")

    def __repr__(self):
        return f"<User(id='{self.id}')>"


class UserLocalAuth(Base):
    __tablename__ = "user_local_auth"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), primary_key=True)
    username: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    
    password_updated_at: Mapped[datetime] = mapped_column(default=func.now(), onupdate=func.now())
    email_updated_at: Mapped[datetime] = mapped_column(default=func.now(), onupdate=func.now())

    user: Mapped["User"] = relationship(back_populates="local_auth")


class UserExternalAuth(Base):
    __tablename__ = "user_external_auth"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)

    provider: Mapped[AuthProviderEnum] = mapped_column(nullable=False)
    provider_user_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    
    provider_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(default=func.now())

    user: Mapped["User"] = relationship(back_populates="external_auths")

    __table_args__ = (
        UniqueConstraint('provider', 'provider_user_id', name='_provider_user_uc'),
    )


class UserRole(Base):
    __tablename__ = "user_roles"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    role: Mapped[UserRoleEnum] = mapped_column(nullable=False)

    user: Mapped[User] = relationship("User", back_populates="roles")

    def __repr__(self):
        return f"<UserRole(id='{self.id}', user_id='{self.user_id}', role='{self.role}', role={self.role})>"


class UserSession(Base):
    __tablename__ = "user_sessions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    jti: Mapped[uuid.UUID] = mapped_column(unique=True, nullable=False, index=True)
    issued_at: Mapped[datetime] = mapped_column(default=func.now(), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(nullable=False)
    user_agent: Mapped[Optional[str]] = mapped_column(nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    user: Mapped[User] = relationship("User", back_populates="sessions")

    def __repr__(self):
        return f"<UserSession(id='{self.id}', user_id='{self.user_id}', jti='{self.jti}', is_active={self.is_active})>"