import logging
import uuid
from typing import Optional

from datetime import timezone
from sqlalchemy import delete, or_, select, update
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User, UserRole, UserRoleEnum, UserSession, UserLocalAuth
from app.schemas import UserCreateRequest
from app.permissions import ROLES_PERMISSIONS

from datetime import datetime

logger = logging.getLogger(__name__)


async def is_email_taken(db: AsyncSession, email: str) -> bool:
    stmt = select(UserLocalAuth.user_id).where(UserLocalAuth.email == email)
    result = await db.execute(stmt)
    return result.scalar_one_or_none() is not None


async def is_username_taken(db: AsyncSession, username: str) -> bool:
    stmt = select(UserLocalAuth.user_id).where(UserLocalAuth.username == username)
    result = await db.execute(stmt)
    return result.scalar_one_or_none() is not None


async def get_user_by_id(db: AsyncSession, user_id: uuid.UUID) -> Optional[User]:
    stmt = (
        select(User)
        .options(selectinload(User.roles))
        .where(User.id == user_id)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_local_auth_by_identifier(db: AsyncSession, identifier: str) -> Optional[UserLocalAuth]:
    stmt = (
        select(UserLocalAuth)
        .options(
            joinedload(UserLocalAuth.user).selectinload(User.roles)
        )
        .where(
            or_(
                UserLocalAuth.username == identifier,
                UserLocalAuth.email == identifier
            )
        )
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def create_local_user(
    db: AsyncSession,
    user_id: uuid.UUID,
    user_data: UserCreateRequest,
    password_hash: str,
    verification_code: Optional[str] = None
) -> User:
    try:
        db_user = User(
            id=user_id,
        )
        db.add(db_user)

        db_local_auth = UserLocalAuth(
            user_id=user_id,
            email=user_data.email,
            username=user_data.username,
            password_hash=password_hash,
            verification_code=verification_code
        )
        db.add(db_local_auth)

        db_role = UserRole(
            user_id=user_id,
            role=UserRoleEnum.USER
        )
        db.add(db_role)

        await db.commit()
        await db.refresh(db_user)
        return db_user

    except IntegrityError as e:
        await db.rollback()
        logger.error(f"Integrity error during user creation: {e}")
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Unexpected error during user creation: {e}")
        raise


async def create_user_session(
    db: AsyncSession,
    user_id: uuid.UUID,
    refresh_token_jti: uuid.UUID,
    access_token_jti: uuid.UUID,
    issued_at: datetime,
    expires_at: datetime,
    user_agent: Optional[str] = None,
    ip_address: Optional[str] = None,
) -> UserSession:
    logger.info(f"Creating new user session: {user_id}")
    db_session = UserSession(
        user_id=user_id,
        refresh_token_jti=refresh_token_jti,
        access_token_jti=access_token_jti,
        issued_at=issued_at,
        expires_at=expires_at,
        user_agent=user_agent,
        ip_address=ip_address,
    )
    db.add(db_session)
    try:
        await db.commit()
        logger.info(f"Successfully created session: {db_session}")
        await db.refresh(db_session)
        return db_session
    except IntegrityError as e:
        await db.rollback()
        logger.error(f"Integrity error during user's session creation: {e}")
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Unexpected error during user's session creation: {e}")
        raise


async def mark_email_as_verified(db: AsyncSession, user_id: uuid.UUID):
    stmt = (
        update(UserLocalAuth)
        .where(UserLocalAuth.user_id == user_id)
        .values(
            email_verified_at=datetime.now(timezone.utc),
            verification_code=None
        )
    )
    await db.execute(stmt)
    await db.commit()


async def get_user_by_verification_code(db: AsyncSession, code: str) -> Optional[UserLocalAuth]:
    stmt = select(UserLocalAuth).where(UserLocalAuth.verification_code == code)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def create_session(
    db: AsyncSession,
    user_id: uuid.UUID,
    access_token_jti: uuid.UUID,
    refresh_token_jti: uuid.UUID,
    expires_at: datetime,
    user_agent: Optional[str] = None,
    ip_address: Optional[str] = None,
) -> UserSession:
    db_session = UserSession(
        user_id=user_id,
        access_token_jti=access_token_jti,
        refresh_token_jti=refresh_token_jti,
        expires_at=expires_at,
        user_agent=user_agent,
        ip_address=ip_address,
    )
    db.add(db_session)
    await db.commit()
    await db.refresh(db_session)
    return db_session


async def get_active_session(db: AsyncSession, session_id: uuid.UUID) -> Optional[UserSession]:
    stmt = select(UserSession).where(
        UserSession.id == session_id,
        UserSession.is_active == True,
        UserSession.expires_at > datetime.now(timezone.utc)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def deactivate_session(db: AsyncSession, session_id: uuid.UUID):
    stmt = (
        update(UserSession)
        .where(UserSession.id == session_id)
        .values(is_active=False)
    )
    await db.execute(stmt)
    await db.commit()


async def deactivate_all_user_sessions(db: AsyncSession, user_id: uuid.UUID):
    stmt = (
        update(UserSession)
        .where(UserSession.user_id == user_id, UserSession.is_active == True)
        .values(is_active=False)
    )
    await db.execute(stmt)
    await db.commit()


async def get_role_permissions(role: str) -> list[str]: 
    return ROLES_PERMISSIONS.get(role, [])