import uuid

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import create_user_profile
from app.schemas import UserProfileCreate

TEST_USERNAME = "current_contact_owner"


@pytest.mark.asyncio(loop_scope="session")
async def test_add_friend(
    client: TestClient, db_session: AsyncSession, mock_file_upload_client
):
    user_profile = await create_user_profile(
        db_session, UserProfileCreate(username=TEST_USERNAME)
    )
    friend_profile = await create_user_profile(
        db_session, UserProfileCreate(username="testfriend")
    )

    response = await client.post(
        f"/api/v1/users/me/contacts/{friend_profile.id}/friend",
        headers={"X-User-Id": str(user_profile.id)},
    )
    assert response.status_code == 200
    assert response.json()["contact_user_id"] == str(friend_profile.id)
    assert response.json()["status"] == "FRIEND"


@pytest.mark.asyncio
async def test_block_user(
    client: httpx.AsyncClient, db_session: AsyncSession, mock_file_upload_client
):
    user_profile = await create_user_profile(
        db_session, UserProfileCreate(username=TEST_USERNAME)
    )
    blocked_profile = await create_user_profile(
        db_session, UserProfileCreate(username="testblocked")
    )

    response = await client.post(
        f"/api/v1/users/me/contacts/{blocked_profile.id}/block",
        headers={"X-User-Id": str(user_profile.id)},
    )
    assert response.status_code == 200
    assert response.json()["contact_user_id"] == str(blocked_profile.id)
    assert response.json()["status"] == "BLOCKED"


@pytest.mark.asyncio
async def test_remove_contact(client: httpx.AsyncClient, db_session: AsyncSession):
    user_profile = await create_user_profile(
        db_session, UserProfileCreate(username=TEST_USERNAME)
    )
    contact_profile = await create_user_profile(
        db_session, UserProfileCreate(username="temp_contact")
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
    client: httpx.AsyncClient, db_session: AsyncSession, mock_file_upload_client
):
    user_profile = await create_user_profile(
        db_session, UserProfileCreate(username=TEST_USERNAME)
    )
    friend_profile = await create_user_profile(
        db_session, UserProfileCreate(username="friend1")
    )
    blocked_profile = await create_user_profile(
        db_session, UserProfileCreate(username="blocked1")
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
        c for c in contacts if c["contact_user_id"] == str(friend_profile.id)
    )
    assert friend_contact["status"] == "FRIEND"
    assert friend_contact["username"] == "friend1"
    assert friend_contact["avatar_url"] == None

    blocked_contact = next(
        c for c in contacts if c["contact_user_id"] == str(blocked_profile.id)
    )
    assert blocked_contact["status"] == "BLOCKED"
