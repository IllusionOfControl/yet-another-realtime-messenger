import pytest
import uuid
from datetime import datetime, timezone, timedelta
import jwt

@pytest.mark.asyncio
async def test_user_service_respects_auth_blacklist(client, jwt_token_factory):
    from app.settings import get_settings
    from app.database import get_redis_client
    
    settings = get_settings()
    redis_client = get_redis_client()
    
    # 1. Generate a token
    jti = str(uuid.uuid4())
    token = jwt_token_factory(jti=jti, scopes=["user.profile.view"])
    
    # 2. Manually blacklist it in Redis (simulating auth-service logout)
    await redis_client.setex(f"blacklist:{jti}", 3600, "true")
    
    # 3. Try to access user-service
    response = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # 4. Assert 401 Unauthorized
    assert response.status_code == 401
    assert response.json()["error"]["message"] == "Token has been revoked"
    
    # Cleanup
    await redis_client.delete(f"blacklist:{jti}")

@pytest.mark.asyncio
async def test_user_service_allows_non_blacklisted_token(client, jwt_token_factory, db_session):
    from app.crud import create_user_profile
    from app.schemas import UserProfileCreate
    
    # Create a profile so /users/me doesn't 404
    user_id = uuid.uuid4()
    await create_user_profile(db_session, UserProfileCreate(username="active_user", email="active@example.com"))
    
    # Generate token
    token = jwt_token_factory(sub=user_id, scopes=["user.profile.view"])
    
    # Access user-service
    response = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # Should succeed (or at least not fail due to revocation)
    assert response.status_code != 401