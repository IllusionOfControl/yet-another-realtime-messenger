import uuid
from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=func.now())
    password_updated_at: Mapped[datetime] = mapped_column(
        default=func.now(), onupdate=func.now()
    )
    email_updated_at: Mapped[datetime] = mapped_column(
        default=func.now(), onupdate=func.now()
    )

    # Refresh token management (optional, can be in Redis instead)
    # refresh_tokens = relationship("RefreshToken", back_populates="user", lazy="selectin")

    def __repr__(self):
        return f"<User(id='{self.id}', email='{self.email}')>"
