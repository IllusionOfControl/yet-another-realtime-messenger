import pytest
import uuid
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import create_local_user, is_email_taken, is_username_taken, get_active_session, get_local_auth_by_identifier, get_user_by_id, get_user_by_verification_code, create_session, deactivate_session, deactivate_all_user_sessions, mark_email_as_verified
from app.models import UserRoleEnum
from app.schemas import UserCreateRequest


@pytest.mark.asyncio
async def test_create_local_user_success(db_session: AsyncSession):
    user_id = uuid.uuid4()
    user_data = UserCreateRequest(
        username="test_user",
        email="test@example.com",
        password="secret_password",
        display_name="Test Display"
    )
    password_hash = "hashed_content"
    code = "verify_123"

    user = await create_local_user(
        db_session, user_id, user_data, password_hash, verification_code=code
    )

    assert user.id == user_id
    
    assert user.local_auth.username == "test_user"
    assert user.local_auth.email == "test@example.com"
    assert user.local_auth.password_hash == password_hash
    assert user.local_auth.verification_code == code
    assert len(user.roles) == 1
    assert user.roles[0].role == UserRoleEnum.USER


@pytest.mark.asyncio
async def test_is_username_email_taken(db_session: AsyncSession):
    user_id = uuid.uuid4()
    user_data = UserCreateRequest(username="unique_guy", email="unique@mail.com", password="123456")
    await create_local_user(db_session, user_id, user_data, "hash")

    assert await is_username_taken(db_session, "unique_guy") is True
    assert await is_username_taken(db_session, "other_guy") is False
    assert await is_email_taken(db_session, "unique@mail.com") is True
    assert await is_email_taken(db_session, "other@mail.com") is False


@pytest.mark.asyncio
async def test_get_local_auth_by_identifier(db_session: AsyncSession):
    user_id = uuid.uuid4()
    username = "login_nick"
    email = "login@email.com"
    user_data = UserCreateRequest(username=username, email=email, password="123456")
    await create_local_user(db_session, user_id, user_data, "hash")

    auth_by_nick = await get_local_auth_by_identifier(db_session, username)
    assert auth_by_nick is not None
    assert auth_by_nick.user_id == user_id
    assert auth_by_nick.username == username

    auth_by_email = await get_local_auth_by_identifier(db_session, email)
    assert auth_by_email is not None
    assert auth_by_email.user_id == user_id
    assert auth_by_email.email == email

    assert await get_local_auth_by_identifier(db_session, "unknown") is None

@pytest.mark.asyncio
async def test_email_verification_flow(db_session: AsyncSession):
    user_id = uuid.uuid4()
    code = "secret_code"
    user_data = UserCreateRequest(username="verify_me", email="v@mail.com", password="123456")
    await create_local_user(
        db_session, 
        user_id, 
        user_data, 
        "hash", 
        verification_code=code
    )

    auth_record = await get_user_by_verification_code(db_session, code)
    assert auth_record.user_id == user_id
    assert auth_record.email_verified_at is None

    await mark_email_as_verified(db_session, user_id)

    updated_auth = await get_user_by_id(db_session, user_id)
    assert updated_auth.local_auth.email_verified_at is not None
    assert updated_auth.local_auth.verification_code is None



@pytest.mark.asyncio
async def test_session_lifecycle(db_session: AsyncSession):
    user_id = uuid.uuid4()
    await create_local_user(
        db_session, 
        user_id, 
        UserCreateRequest(
            username="sess", 
            email="s@m.com", 
            password="123456"
        ), "h"
    )

    access_token_jti = uuid.uuid4()
    refresh_token_jti = uuid.uuid4()
    expires = datetime.now(timezone.utc) + timedelta(days=1)

    session = await create_session(
        db_session, 
        user_id, 
        access_token_jti,
        refresh_token_jti,
        expires, 
        "Mozilla", 
        "127.0.0.1"
    )
    assert session.access_token_jti == access_token_jti
    assert session.refresh_token_jti == refresh_token_jti
    assert session.is_active is True

    active_sess = await get_active_session(db_session, session.id)
    assert active_sess is not None
    assert active_sess.user_id == user_id

    await deactivate_session(db_session, session.id)
    assert await get_active_session(db_session, session.id) is None


@pytest.mark.asyncio
async def test_deactivate_all_sessions(db_session: AsyncSession):
    user_id = uuid.uuid4()
    await create_local_user(db_session, user_id, 
                               UserCreateRequest(username="multi", email="m@m.com", password="123456"), "h")
    
    await create_session(
        db_session, 
        user_id, 
        uuid.uuid4(), 
        uuid.uuid4(),
        datetime.now(timezone.utc) + timedelta(1),
    )
    await create_session(
        db_session, 
        user_id, 
        uuid.uuid4(), 
        uuid.uuid4(),
        datetime.now(timezone.utc) + timedelta(1),
    )

    await deactivate_all_user_sessions(db_session, user_id)

    from sqlalchemy import select
    from app.models import UserSession
    stmt = select(UserSession).where(UserSession.user_id == user_id, UserSession.is_active == True)
    result = await db_session.execute(stmt)
    assert len(result.scalars().all()) == 0