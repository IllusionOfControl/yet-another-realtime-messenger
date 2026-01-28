import pytest


@pytest.mark.asyncio
async def test_full_auth_flow(client, db_session):
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "strongpassword123",
        "display_name": "Tester",
    }

    reg_resp = await client.post("/api/v1/auth/register", json=user_data)
    assert reg_resp.status_code == 201
    assert "verify your email" in reg_resp.json()["message"]

    from sqlalchemy import select

    from app.models import UserLocalAuth

    res = await db_session.execute(
        select(UserLocalAuth).where(UserLocalAuth.email == user_data["email"])
    )
    local_auth = res.scalar_one()
    verification_code = local_auth.verification_code

    verify_resp = await client.post(
        "/api/v1/auth/verify-email", params={"code": verification_code}
    )
    assert verify_resp.status_code == 200

    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"login": user_data["email"], "password": user_data["password"]},
    )
    assert login_resp.status_code == 200
    tokens = login_resp.json()
    assert "access_token" in tokens
    assert "refresh_token" in tokens

    access_token = tokens["access_token"]
    refresh_token = tokens["refresh_token"]

    val_resp = await client.post(
        "/api/v1/auth/validate-token",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert val_resp.status_code == 200

    ref_resp = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": refresh_token}
    )
    assert ref_resp.status_code == 200
    assert ref_resp.json()["access_token"] != access_token

    login_username_resp = await client.post(
        "/api/v1/auth/login",
        json={"login": user_data["username"], "password": user_data["password"]},
    )
    assert login_username_resp.status_code == 200

    logout_resp = await client.post(
        "/api/v1/auth/logout",
        json={"all_devices": False},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert logout_resp.status_code == 204


@pytest.mark.asyncio
async def test_login_invalid_credentials(client):
    resp = await client.post(
        "/api/v1/auth/login", json={"login": "wronguser", "password": "wrongpassword"}
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_register_duplicate_email(client, db_session):
    user_data = {
        "username": "user1",
        "email": "dup@example.com",
        "password": "password123",
    }
    
    await client.post("/api/v1/auth/register", json=user_data)
    
    resp = await client.post(
        "/api/v1/auth/register",
        json={
            "username": "user2",
            "email": "dup@example.com",
            "password": "password123",
        },
    )
    assert resp.status_code == 409
    print(resp.json())
    assert "Email already registered" in resp.json()["error"]["message"]


@pytest.mark.asyncio
async def test_verify_email_invalid_code(client):
    resp = await client.post("/api/v1/auth/verify-email", params={"code": "wrong-code"})
    assert resp.status_code == 400
    assert "Invalid or expired" in resp.json()["error"]["message"]
