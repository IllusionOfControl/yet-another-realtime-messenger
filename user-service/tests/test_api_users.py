import uuid

import httpx
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import create_user_profile
from app.schemas import UserProfileCreate, UserProfileUpdate


@pytest.mark.asyncio
async def test_create_user_profile_internal(
    client: httpx.AsyncClient, db_session: AsyncSession
):
    response = await client.post(
        "/api/v1/users/internal/create-profile",
        json={
            "username": "newuser",
            "display_name": "New User",
            "email": "new@example.com",
        },
    )
    assert response.status_code == 201
    assert response.json()["id"]
    assert response.json()["username"] == "newuser"


@pytest.mark.asyncio
async def test_read_users_me(
    client: httpx.AsyncClient, db_session: AsyncSession, mock_file_upload_client
):
    username="testuser"
    display_name = "Test User"
    email="testuser@example.com"

    user_profile = await create_user_profile(
        db_session, UserProfileCreate(username=username, display_name=display_name, email=email)
    )

    response = await client.get(
        "/api/v1/users/me", headers={"X-User-Id": str(user_profile.id)}
    )
    assert response.status_code == 200
    assert response.json()["username"] == username
    mock_file_upload_client.get_signed_url.assert_not_called()


@pytest.mark.asyncio
async def test_update_users_me(
    client: httpx.AsyncClient, db_session: AsyncSession, mock_file_upload_client
):
    username="testuser"
    display_name = "Test User"
    email="testuser@example.com"

    user_profile = await create_user_profile(
        db_session, UserProfileCreate(username=username, display_name=display_name, email=email)
    )

    updated_display_name = "Updated Display"
    updated_bio="My new bio"
    
    update_data = UserProfileUpdate(
        display_name=updated_display_name, bio=updated_bio
    )
    response = await client.put(
        "/api/v1/users/me",
        headers={"X-User-Id": str(user_profile.id)},
        json=update_data.model_dump(exclude_unset=True),
    )
    assert response.status_code == 200
    assert response.json()["display_name"] == updated_display_name
    assert response.json()["bio"] == updated_bio


@pytest.mark.asyncio
async def test_upload_user_avatar(
    client: httpx.AsyncClient, db_session: AsyncSession, mock_file_upload_client
):
    username="testuser"
    display_name = "Test User"
    email="testuser@example.com"

    user_profile = await create_user_profile(
        db_session, UserProfileCreate(username=username, display_name=display_name, email=email)
    )


    mock_file_upload_client.upload_file.return_value = {
        "id": str(uuid.uuid4()),
        "original_file_name": "avatar.png",
        "size_bytes": 12345,
        "mime_type": "image/png",
    }

    file_content = b"fake image data"
    response = await client.post(
        "/api/v1/users/me/avatar",
        headers={
            "X-User-Id": str(user_profile.id),
            "Authorization": "Bearer dummy_token",
        },
        files={"file": ("avatar.png", file_content, "image/png")},
    )
    assert response.status_code == 200
    assert response.json()["avatar_url"] == "http://mock_file_upload_service/avatar.jpg"
    mock_file_upload_client.upload_file.assert_called_once()
    mock_file_upload_client.get_signed_url.assert_called_once()


@pytest.mark.asyncio
async def test_read_user_profile(
    client: httpx.AsyncClient,
    db_session: AsyncSession,
):
    username="testuser"
    display_name = "Test User"
    email="testuser@example.com"

    user_profile = await create_user_profile(
        db_session, UserProfileCreate(username=username, display_name=display_name, email=email)
    )

    response = await client.get(f"/api/v1/users/{user_profile.id}")
    assert response.status_code == 200
    assert response.json()["username"] == username


@pytest.mark.asyncio
async def test_search_users(client: httpx.AsyncClient, db_session: AsyncSession):
    user1_profile = await create_user_profile(
        db_session,
        UserProfileCreate(username="searchuser1", display_name="User One", email="user1@example.com"),
    )
    user2_profile = await create_user_profile(
        db_session,
        UserProfileCreate(username="searchuser2", display_name="User Two", email="user2@example.com"),
    )

    response = await client.get("/api/v1/users/search?query=user1")
    print(response.json())
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["username"] == "searchuser1"

    response = await client.get("/api/v1/users/search?query=User&limit=1")
    assert response.status_code == 200
    assert len(response.json()) == 1
