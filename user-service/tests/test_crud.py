import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import (
    add_or_update_contact,
    create_user_profile,
    get_user_contacts,
    get_user_profile_by_id,
    get_user_profile_by_username,
    remove_contact_entry,
    search_user_profiles,
    update_user_profile,
)
from app.models import ContactStatus, UserContact, UserProfile
from app.schemas import UserProfileCreate, UserProfileUpdate


@pytest.mark.asyncio
async def test_create_user_profile(db_session: AsyncSession):
    user_data = UserProfileCreate(
        username="testuser", display_name="Test User", email="test@example.com"
    )
    user_profile = await create_user_profile(db_session, user_data)

    assert user_profile.id
    assert user_profile.username == "testuser"
    assert user_profile.email == "test@example.com"


@pytest.mark.asyncio
async def test_get_user_profile_by_id(db_session: AsyncSession):
    user_data = UserProfileCreate(username="gettest", display_name="Get Test")
    user_profile = await create_user_profile(db_session, user_data)

    retrieved_user = await get_user_profile_by_id(db_session, user_profile.id)
    assert retrieved_user is not None
    assert retrieved_user.username == "gettest"


@pytest.mark.asyncio
async def test_update_user_profile(db_session: AsyncSession):
    user_data = UserProfileCreate(username="updatetest", display_name="Update Test")
    user_profile = await create_user_profile(db_session, user_data)

    update_data = UserProfileUpdate(display_name="Updated Name", bio="New Bio")
    updated_user = await update_user_profile(db_session, user_profile.id, update_data)

    assert updated_user.display_name == "Updated Name"
    assert updated_user.bio == "New Bio"

    check_user = await get_user_profile_by_id(db_session, user_profile.id)
    assert check_user.display_name == "Updated Name"


@pytest.mark.asyncio
async def test_search_user_profiles(db_session: AsyncSession):
    await create_user_profile(
        db_session,
        UserProfileCreate(
            id=uuid.uuid4(), username="alice", display_name="Alice Wonderland"
        ),
    )
    await create_user_profile(
        db_session,
        UserProfileCreate(id=uuid.uuid4(), username="bob", display_name="Bobby Dazler"),
    )
    await create_user_profile(
        db_session,
        UserProfileCreate(
            id=uuid.uuid4(), username="charlie", display_name="Charlie Chaplin"
        ),
    )

    results = await search_user_profiles(db_session, "alic")
    assert len(results) == 1
    assert results[0].username == "alice"

    results = await search_user_profiles(db_session, "bo")
    assert len(results) == 1
    assert results[0].username == "bob"

    results = await search_user_profiles(db_session, "land")
    assert len(results) == 1
    assert results[0].username == "alice"


@pytest.mark.asyncio
async def test_add_friend_contact(db_session: AsyncSession):
    owner_profile = await create_user_profile(
        db_session, UserProfileCreate(username="owner")
    )
    contact_profile = await create_user_profile(
        db_session, UserProfileCreate(username="friend")
    )

    contact = await add_or_update_contact(
        db_session, owner_profile.id, contact_profile.id, ContactStatus.FRIEND
    )
    assert contact.owner_id == owner_profile.id
    assert contact.contact_user_id == contact_profile.id
    assert contact.status == ContactStatus.FRIEND


@pytest.mark.asyncio
async def test_block_user_contact(db_session: AsyncSession):
    owner_profile = await create_user_profile(
        db_session, UserProfileCreate(username="blocker")
    )
    contact_profile = await create_user_profile(
        db_session, UserProfileCreate(username="blocked")
    )

    contact = await add_or_update_contact(
        db_session, owner_profile.id, contact_profile.id, ContactStatus.BLOCKED
    )
    contact = await add_or_update_contact(
        db_session, owner_profile.id, contact_profile.id, ContactStatus.BLOCKED
    )
    assert contact.status == ContactStatus.BLOCKED


@pytest.mark.asyncio
async def test_remove_contact(db_session: AsyncSession):
    owner_profile = await create_user_profile(
        db_session, UserProfileCreate(username="owner_remove")
    )
    contact_profile = await create_user_profile(
        db_session, UserProfileCreate(username="contact_remove")
    )
    await add_or_update_contact(
        db_session, owner_profile.id, contact_profile.id, ContactStatus.FRIEND
    )

    removed = await remove_contact_entry(
        db_session, owner_profile.id, contact_profile.id
    )
    assert removed is True
    assert await get_user_contacts(db_session, owner_profile.id) == []
