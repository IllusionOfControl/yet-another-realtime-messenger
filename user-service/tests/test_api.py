import pytest

@pytest.mark.asyncio
async def test_token_revocation_on_logout(client, db_session, mock_redis_client):
    username="testuser"
    display_name = "Test User"
    email="testuser@example.com"

    user_profile = await create_user_profile(
        db_session, UserProfileCreate(username=username, display_name=display_name, email=email)
    )

    access_token = jwt_token_factory(sub=user_profile.id, scopes=["user.profile.view"])
    
    # 2. Logout
    await client.post(
        "/api/v1/auth/logout", 
        headers={"Authorization": f"Bearer {access_token}"},
        json={"all_devices": False}
    )
    
    # 3. Try to use token again
    response = await client.get(
        "/api/v1/users/me", 
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Token has been revoked"