import uuid
from typing import List, Optional

from sqlalchemy import and_, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ContactStatus, UserContact, UserProfile
from app.schemas import UserProfileCreate, UserProfileUpdate


async def get_user_profile_by_id(
    db: AsyncSession, user_id: uuid.UUID
) -> Optional[UserProfile]:
    stmt = select(UserProfile).where(UserProfile.id == user_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_user_profile_by_username(
    db: AsyncSession, username: str
) -> Optional[UserProfile]:
    stmt = select(UserProfile).where(UserProfile.username == username)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_user_profile_by_email(
    db: AsyncSession, email: str
) -> Optional[UserProfile]:
    if not email:
        return None
    stmt = select(UserProfile).where(UserProfile.email == email)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def create_user_profile(
    db: AsyncSession, user_profile: UserProfileCreate
) -> UserProfile:
    db_user_profile = UserProfile(
        username=user_profile.username,
        display_name=user_profile.display_name,
        email=user_profile.email,
    )
    db.add(db_user_profile)
    await db.commit()
    await db.refresh(db_user_profile)
    return db_user_profile


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
    db_user_profile = await get_user_profile_by_id(db, user_id)
    if db_user_profile:
        db_user_profile.avatar_file_id = file_id
        await db.commit()
        await db.refresh(db_user_profile)
    return db_user_profile


async def search_user_profiles(
    db: AsyncSession, query: str, limit: int = 10, offset: int = 0
) -> List[UserProfile]:
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
    return list(result.scalars().all())


async def get_contact_entry(
    db: AsyncSession, owner_id: uuid.UUID, contact_user_id: uuid.UUID
) -> Optional[UserContact]:
    stmt = select(UserContact).where(
        and_(
            UserContact.owner_id == owner_id,
            UserContact.contact_user_id == contact_user_id,
        )
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def add_or_update_contact(
    db: AsyncSession,
    owner_id: uuid.UUID,
    contact_user_id: uuid.UUID,
    status: ContactStatus,
) -> UserContact:
    existing_contact = await get_contact_entry(db, owner_id, contact_user_id)
    if existing_contact:
        existing_contact.status = status
        await db.commit()
        await db.refresh(existing_contact)
        return existing_contact
    else:
        new_contact = UserContact(
            owner_id=owner_id, contact_user_id=contact_user_id, status=status
        )
        db.add(new_contact)
        try:
            await db.commit()
            await db.refresh(new_contact)
            return new_contact
        except IntegrityError:
            await db.rollback()
            return await add_or_update_contact(db, owner_id, contact_user_id, status)


async def remove_contact_entry(
    db: AsyncSession, owner_id: uuid.UUID, contact_user_id: uuid.UUID
) -> bool:
    contact_entry = await get_contact_entry(db, owner_id, contact_user_id)
    if contact_entry:
        await db.delete(contact_entry)
        await db.commit()
        return True
    return False


async def get_user_contacts(db: AsyncSession, owner_id: uuid.UUID) -> List[UserContact]:
    stmt = select(UserContact).where(UserContact.owner_id == owner_id)
    result = await db.execute(stmt)
    return list(result.scalars().all())
