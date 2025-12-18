import logging
import uuid
from typing import Optional

from sqlalchemy import and_, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ContactStatus, UserContact, UserProfile
from app.schemas import UserProfileCreate, UserProfileUpdate

logger = logging.getLogger(__name__)


async def get_user_profile_by_id(
    db: AsyncSession, user_id: uuid.UUID
) -> Optional[UserProfile]:
    logger.debug(f"Attempting to fetch user profile by ID: {user_id}")
    stmt = select(UserProfile).where(UserProfile.id == user_id)
    result = await db.execute(stmt)
    profile = result.scalar_one_or_none()
    if profile:
        logger.debug(f"Successfully fetched user profile for ID: {user_id}")
    else:
        logger.debug(f"User profile not found for ID: {user_id}")
    return profile


async def get_user_profile_by_username(
    db: AsyncSession, username: str
) -> Optional[UserProfile]:
    logger.debug(f"Attempting to fetch user profile by username: {username}")
    stmt = select(UserProfile).where(UserProfile.username == username)
    result = await db.execute(stmt)
    profile = result.scalar_one_or_none()
    if profile:
        logger.debug(f"Successfully fetched user profile for username: {username}")
    else:
        logger.debug(f"User profile not found for username: {username}")
    return profile


async def get_user_profile_by_email(
    db: AsyncSession, email: str
) -> Optional[UserProfile]:
    logger.debug(f"Attempting to fetch user profile by email: {email}")
    if not email:
        logger.debug("Email is empty, returning None for user profile search.")
        return None
    stmt = select(UserProfile).where(UserProfile.email == email)
    result = await db.execute(stmt)
    profile = result.scalar_one_or_none()
    if profile:
        logger.debug(f"Successfully fetched user profile for email: {email}")
    else:
        logger.debug(f"User profile not found for email: {email}")
    return profile


async def create_user_profile(
    db: AsyncSession, user_profile: UserProfileCreate
) -> UserProfile:
    logger.info(f"Creating new user profile for username: {user_profile.username}")
    db_user_profile = UserProfile(
        username=user_profile.username,
        display_name=user_profile.display_name or user_profile.username,
        email=user_profile.email,
    )
    try:
        db.add(db_user_profile)
        await db.commit()
        await db.refresh(db_user_profile)
        logger.info(f"User profile successfully created with ID: {db_user_profile.id}")
        return db_user_profile
    except IntegrityError as e:
        await db.rollback()
        logger.error(
            f"Integrity error when creating user profile for {user_profile.username}: {e}",
            exc_info=True,
        )
        raise


async def update_user_profile(
    db: AsyncSession, user_id: uuid.UUID, user_profile_update: UserProfileUpdate
) -> Optional[UserProfile]:
    db_user_profile = await get_user_profile_by_id(db, user_id)
    if db_user_profile:
        update_data = user_profile_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_user_profile, key, value)
        await db.commit()
        await db.refresh(db_user_profile)
    return db_user_profile


async def update_user_avatar(
    db: AsyncSession, user_id: uuid.UUID, file_id: uuid.UUID
) -> Optional[UserProfile]:
    logger.info(
        f"Attempting to update avatar for user ID: {user_id} with file ID: {file_id}"
    )
    db_user_profile = await get_user_profile_by_id(db, user_id)
    if db_user_profile:
        db_user_profile.avatar_file_id = file_id
        await db.commit()
        await db.refresh(db_user_profile)
        logger.info(
            f"Avatar for user {user_id} successfully updated to file ID: {file_id}"
        )
    else:
        logger.warning(
            f"User profile not found for ID: {user_id}. Cannot update avatar."
        )
    return db_user_profile


async def search_user_profiles(
    db: AsyncSession, query: str, limit: int = 10, offset: int = 0
) -> list[UserProfile]:
    logger.debug(
        f"Searching user profiles for query: '{query}', limit: {limit}, offset: {offset}"
    )
    search_pattern = f"%{query}%"
    stmt = (
        select(UserProfile)
        .where(
            or_(
                UserProfile.username.ilike(search_pattern),
                UserProfile.display_name.ilike(search_pattern),
                UserProfile.email.ilike(search_pattern),
            )
        )
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(stmt)
    profiles = list(result.scalars().all())
    logger.debug(f"Found {len(profiles)} user profiles for query: '{query}'")
    return profiles


async def get_contact_entry(
    db: AsyncSession, owner_id: uuid.UUID, contact_id: uuid.UUID
) -> Optional[UserContact]:
    stmt = select(UserContact).where(
        and_(
            UserContact.owner_id == owner_id,
            UserContact.contact_id == contact_id,
        )
    )
    result = await db.execute(stmt)
    contact = result.scalar_one_or_none()
    if contact:
        logger.debug(
            f"Contact entry found for {owner_id} and {contact_id} with status: {contact.status.name}"
        )
    else:
        logger.debug(f"No contact entry found for {owner_id} and {contact_id}")
    return contact


async def add_or_update_contact(
    db: AsyncSession,
    owner_id: uuid.UUID,
    contact_id: uuid.UUID,
    status: ContactStatus,
) -> UserContact:
    logger.info(
        f"Attempting to add or update contact for owner {owner_id} with user {contact_id}, status: {status.name}"
    )
    existing_contact = await get_contact_entry(db, owner_id, contact_id)
    if existing_contact:
        logger.debug(
            f"Existing contact found, updating status from {existing_contact.status.name} to {status.name}"
        )
        existing_contact.status = status
        await db.commit()
        await db.refresh(existing_contact)
        logger.info(
            f"Contact for {owner_id} and {contact_id} updated to status: {status.name}"
        )
        return existing_contact
    else:
        logger.debug(
            f"No existing contact found, creating new entry with status: {status.name}"
        )
        new_contact = UserContact(
            owner_id=owner_id, contact_id=contact_id, status=status
        )
        db.add(new_contact)
        try:
            await db.commit()
            await db.refresh(new_contact)
            logger.info(
                f"New contact for {owner_id} and {contact_id} created with status: {status.name}"
            )
            return new_contact
        except IntegrityError:
            await db.rollback()
            logger.warning(
                f"Integrity error (race condition likely) when adding contact for {owner_id} and {contact_id}. Retrying...",
                exc_info=True,
            )
            return await add_or_update_contact(db, owner_id, contact_id, status)


async def remove_contact_entry(
    db: AsyncSession, owner_id: uuid.UUID, contact_id: uuid.UUID
) -> bool:
    logger.info(
        f"Attempting to remove contact entry for owner {owner_id} and contact {contact_id}"
    )
    contact_entry = await get_contact_entry(db, owner_id, contact_id)
    if contact_entry:
        await db.delete(contact_entry)
        await db.commit()
        logger.info(
            f"Contact entry for {owner_id} and {contact_id} successfully removed."
        )
        return True
    else:
        logger.warning(
            f"Contact entry not found for owner {owner_id} and contact {contact_id}. No action taken."
        )
    return False


async def get_user_contacts(db: AsyncSession, owner_id: uuid.UUID) -> list[UserContact]:
    logger.debug(f"Fetching all contact entries for owner ID: {owner_id}")
    stmt = select(UserContact).where(UserContact.owner_id == owner_id)
    result = await db.execute(stmt)
    contacts = list(result.scalars().all())
    logger.debug(f"Found {len(contacts)} contact entries for owner ID: {owner_id}")
    return contacts
