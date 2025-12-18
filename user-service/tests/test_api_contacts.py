import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import create_user_profile
from app.schemas import UserProfileCreate


@pytest.mark.asyncio(loop_scope="session")
async def test_add_friend(
    client: TestClient, db_session: AsyncSession, mock_file_upload_client
):
    username_user="testuser"
    display_name_user = "Test User"
    email_user="testuser@example.com"

    username_friend="testuser_friend"
    display_name_friend = "Test User Friend"
    email_friend="testuser_friend@example.com"

    user_profile = await create_user_profile(
        db_session, UserProfileCreate(username=username_user, display_name=display_name_user, email=email_user)
    )
    friend_profile = await create_user_profile(
        db_session, UserProfileCreate(username=username_friend, display_name=display_name_friend, email=email_friend)
    )

    response = await client.post(
        f"/api/v1/users/me/contacts/{friend_profile.id}/friend",
        headers={"X-User-Id": str(user_profile.id)},
    )
    assert response.status_code == 200
    assert response.json()["contact_id"] == str(friend_profile.id)
    assert response.json()["status"] == "FRIEND"


@pytest.mark.asyncio
async def test_block_user(
    client: httpx.AsyncClient, db_session: AsyncSession, mock_file_upload_client
):
    username_user="testuser"
    display_name_user = "Test User"
    email_user="testuser@example.com"

    username_blocked="testuser_blocked"
    display_name_blocked = "Test User Blocked"
    email_blocked="testuser_blocked@example.com"

    user_profile = await create_user_profile(
        db_session, UserProfileCreate(username=username_user, display_name=display_name_user, email=email_user)
    )
    blocked_profile = await create_user_profile(
        db_session, UserProfileCreate(username=username_blocked, display_name=display_name_blocked, email=email_blocked)
    )

    response = await client.post(
        f"/api/v1/users/me/contacts/{blocked_profile.id}/block",
        headers={"X-User-Id": str(user_profile.id)},
    )
    assert response.status_code == 200
    assert response.json()["contact_id"] == str(blocked_profile.id)
    assert response.json()["status"] == "BLOCKED"


@pytest.mark.asyncio
async def test_remove_contact(client: httpx.AsyncClient, db_session: AsyncSession):
    username_user="testuser"
    display_name_user = "Test User"
    email_user="testuser@example.com"

    username_friend="testuser_friend"
    display_name_friend = "Test User Friend"
    email_friend="testuser_friend@example.com"

    user_profile = await create_user_profile(
        db_session, UserProfileCreate(username=username_user, display_name=display_name_user, email=email_user)
    )
    contact_profile = await create_user_profile(
        db_session, UserProfileCreate(username=username_friend, display_name=display_name_friend, email=email_friend)
    )

    await client.post(
        f"/api/v1/users/me/contacts/{contact_profile.id}/friend",
        headers={"X-User-Id": str(user_profile.id)},
    )

    response = await client.delete(
        f"/api/v1/users/me/contacts/{contact_profile.id}",
        headers={"X-User-Id": str(user_profile.id)},
    )
    assert response.status_code == 204

    get_response = await client.get(
        "/api/v1/users/me/contacts", headers={"X-User-Id": str(user_profile.id)}
    )
    assert get_response.status_code == 200
    assert len(get_response.json()) == 0


@pytest.mark.asyncio
async def test_get_my_contacts(
    client: httpx.AsyncClient, db_session: AsyncSession,
):
    username_user="testuser"
    display_name_user = "Test User"
    email_user="testuser@example.com"

    username_friend="testuser_friend"
    display_name_friend = "Test User Friend"
    email_friend="testuser_friend@example.com"

    username_blocked="testuser_blocked"
    display_name_blocked = "Test User Blocked"
    email_blocked="testuser_blocked@example.com"

    user_profile = await create_user_profile(
        db_session, UserProfileCreate(username=username_user, display_name=display_name_user, email=email_user)
    )
    friend_profile = await create_user_profile(
        db_session, UserProfileCreate(username=username_friend, display_name=display_name_friend, email=email_friend)
    )
    blocked_profile = await create_user_profile(
        db_session, UserProfileCreate(username=username_blocked, display_name=display_name_blocked, email=email_blocked)
    )

    await client.post(
        f"/api/v1/users/me/contacts/{friend_profile.id}/friend",
        headers={"X-User-Id": str(user_profile.id)},
    )
    await client.post(
        f"/api/v1/users/me/contacts/{blocked_profile.id}/block",
        headers={"X-User-Id": str(user_profile.id)},
    )

    response = await client.get(
        "/api/v1/users/me/contacts", headers={"X-User-Id": str(user_profile.id)}
    )
    assert response.status_code == 200
    contacts = response.json()
    assert len(contacts) == 2

    friend_contact = next(
        c for c in contacts if c["contact_id"] == str(friend_profile.id)
    )
    assert friend_contact["status"] == "FRIEND"
    assert friend_contact["username"] == username_friend
    assert friend_contact["avatar_url"] == None

    blocked_contact = next(
        c for c in contacts if c["contact_id"] == str(blocked_profile.id)
    )
    assert blocked_contact["status"] == "BLOCKED"
