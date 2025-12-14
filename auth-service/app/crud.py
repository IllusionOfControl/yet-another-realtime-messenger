import logging
import uuid
from typing import Optional

from sqlalchemy import delete, insert, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User
from app.schemas import UserCreateRequest

logger = logging.getLogger(__name__)


async def get_user_by_id(db: AsyncSession, user_id: uuid.UUID) -> Optional[User]:
    logger.debug(f"Attempting to retrieve user by ID: {user_id}")
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if user:
        logger.debug(f"User found by ID: {user_id}")
    else:
        logger.debug(f"User not found by ID: {user_id}")
    return user


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    if not email:
        logger.debug("Attempted to retrieve user by empty email. Skipping.")
        return None
    logger.debug(f"Attempting to retrieve user by email: {email}")
    stmt = select(User).where(User.email == email)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if user:
        logger.debug(f"User found by email: {email} (ID: {user.id})")
    else:
        logger.debug(f"User not found by email: {email}")
    return user


async def get_user_by_username_or_email(
    db: AsyncSession, identifier: str
) -> Optional[User]:
    logger.debug(f"Attempting to retrieve user by username or email: {identifier}")
    stmt = select(User).where(
        or_(
            User.username == identifier,
            User.email == identifier if "@" in identifier else False,
        )
    )
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if user:
        logger.debug(f"User found by identifier: {identifier} (ID: {user.id})")
    else:
        logger.debug(f"User not found by identifier: {identifier}")
    return user


async def create_user(
    db: AsyncSession,
    user_id: uuid.UUID,
    user_data: UserCreateRequest,
    password_hash: str,
) -> User:
    logger.info(f"Attempting to create new user: {user_data.username}")
    db_user = User(
        id=user_id,
        email=user_data.email,
        password_hash=password_hash,
    )
    db_user
    db.add(db_user)
    try:
        await db.commit()
        await db.refresh(db_user)
        logger.info(f"Successfully created user with email: {db_user}")
        return db_user
    except IntegrityError as e:
        await db.rollback()
        logger.error(
            f"Failed to create user {user_data.username} due to integrity error: {e}"
        )
        raise
    except Exception as e:
        await db.rollback()
        logger.error(
            f"An unexpected error occurred while creating user {user_data.username}: {e}",
            exc_info=True,
        )
        raise


async def delete_user(db: AsyncSession, user_id: uuid.UUID) -> None:
    logger.info(f"Attempting to delete user with id: {str(user_id)}")

    stmt = delete(User).where(id=user_id)
    await db.execute(stmt)
