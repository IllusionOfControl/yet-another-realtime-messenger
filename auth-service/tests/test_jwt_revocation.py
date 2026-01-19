import pytest
import uuid
from datetime import datetime, timezone, timedelta
from app.security import create_access_token

@pytest.mark.asyncio
async def test_logout_blacklists_token_successfully(client, mock_redis_client, db_session):
    # 1. Create a valid token manually to control JTI and EXP
    settings = db_session.bind.url # Just to get access to settings if needed, but we use get_settings
    from app.settings import get_settings
    conf = get_settings()
    
    jti = str(uuid.uuid4())
    sid = str(uuid.uuid4())
    sub = str(uuid.uuid4())
    issued_at = datetime.now(timezone.utc)
    expires_at = issued_at + timedelta(minutes=15)
    
    token = create_access_token(
        data={"sub": sub, "sid": sid, "jti": jti, "scopes": ["user.profile.view"]},
        secret_key=conf.secret_key,
        issued_at=issued_at,
        expires_at=expires_at
    )

    # 2. Call Logout
    response = await client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {token}"},
        json={"all_devices": False}
    )
    assert response.status_code == 204

    # 3. Verify JTI is in Redis
    is_blacklisted = await mock_redis_client.exists(f"blacklist:{jti}")
    assert is_blacklisted == 1

    # 4. Verify subsequent request with same token fails
    # We use the validate-token endpoint which uses get_current_user_data
    bad_response = await client.post(
        "/api/v1/auth/validate-token",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert bad_response.status_code == 401
    assert bad_response.json()["error"]["message"] == "Token has been revoked"

@pytest.mark.asyncio
async def test_logout_all_devices_deactivates_session(client, db_session):
    # This test verifies the DB side of the logout logic
    from app.models import UserSession, User, UserLocalAuth
    from app.schemas import UserCreateRequest
    from app.crud import create_local_user, create_user_session
    
    # Setup user and session
    user_id = uuid.uuid4()
    await create_local_user(db_session, user_id, UserCreateRequest(username="logout_man", email="l@m.com", password="password123"), "hash")
    
    access_jti = uuid.uuid4()
    refresh_jti = uuid.uuid4()
    session = await create_user_session(db_session, user_id, access_jti, refresh_jti, datetime.now(timezone.utc), datetime.now(timezone.utc) + timedelta(days=1))
    
    from app.settings import get_settings
    conf = get_settings()
    token = create_access_token(
        data={"sub": str(user_id), "sid": str(session.id), "jti": str(access_jti), "scopes": []},
        secret_key=conf.secret_key,
        issued_at=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=15)
    )

    # Logout all devices
    await client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {token}"},
        json={"all_devices": True}
    )

    # Verify session is inactive in DB
    from sqlalchemy import select
    res = await db_session.execute(select(UserSession).where(UserSession.user_id == user_id))
    sessions = res.scalars().all()
    for s in sessions:
        assert s.is_active is False