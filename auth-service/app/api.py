import uuid
from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import (
    create_local_user,
    create_user_session,
    deactivate_all_user_sessions,
    deactivate_session,
    get_active_session,
    get_local_auth_by_identifier,
    get_role_permissions,
    get_user_by_verification_code,
    is_email_taken,
    is_username_taken,
    mark_email_as_verified,
    update_session_after_refresh,
)
from app.database import get_db
from app.dependencies import get_current_user_data
from app.schemas import (
    LogoutRequest,
    RefreshTokenRequest,
    SuccessResponse,
    TokenData,
    TokenResponse,
    TokenValidationResponse,
    UserCreateRequest,
    UserLoginRequest,
)
from app.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    verify_password,
)
from app.services.user_client import UserClient, UserClientError, get_user_client
from app.settings import Settings, get_settings
from app.utils import generate_random_sequence

router = APIRouter(prefix="/api/v1/")


@router.post("/health")
async def health():
    return {"status": "ok"}


@router.post(
    "/auth/register",
    response_model=SuccessResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register_user(
    user_create: UserCreateRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    user_client: Annotated[UserClient, Depends(get_user_client)],
):
    if await is_email_taken(db, user_create.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Email already registered"
        )

    if await is_username_taken(db, user_create.username):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Username already registered"
        )

    try:
        user_profile = await user_client.create_user_profile(
            username=user_create.username,
            display_name=user_create.display_name,
            email=user_create.email,
        )
    except UserClientError as e:
        if e.status_code == status.HTTP_409_CONFLICT:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=e.detail)
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user profile in User Service",
            )

    hashed_password = get_password_hash(user_create.password)
    verification_code = generate_random_sequence()
    await create_local_user(
        db,
        user_profile.id,
        user_create,
        hashed_password,
        verification_code,
    )

    # TODO: Отправить Kafka событие для Notification Service, чтобы тот выслал письмо с кодом

    return SuccessResponse(
        message="User registered successfully. Please verify your email."
    )


@router.post("/auth/login", response_model=TokenResponse)
async def login_for_access_token(
    user_login: UserLoginRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
    user_client: Annotated[UserClient, Depends(get_user_client)],
):
    local_auth = await get_local_auth_by_identifier(db, user_login.login)

    if not local_auth or not verify_password(
        user_login.password, local_auth.password_hash
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect login or password",
        )

    user = local_auth.user

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user"
        )

    scopes_set = set()
    for role in user.roles:
        scopes_set.union(await get_role_permissions(role.role))
    scopes = list(scopes_set)

    if local_auth.email_verified_at is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Verify email"
        )

    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    refresh_token_expires = timedelta(days=settings.refresh_token_expire_days)

    issued_at = datetime.now(timezone.utc)
    access_token_expires_at = issued_at + access_token_expires
    refresh_token_expires_at = issued_at + refresh_token_expires

    access_jti = uuid.uuid4()
    refresh_jti = uuid.uuid4()

    user_session = await create_user_session(
        db,
        local_auth.user_id,
        access_jti,
        refresh_jti,
        issued_at,
        refresh_token_expires_at,
    )

    token_data = {
        "sub": str(user.id),
        "scopes": scopes,
        "sid": str(user_session.id),
    }
    access_token = create_access_token(
        data={**token_data, "jti": str(access_jti)},
        secret_key=settings.secret_key,
        issued_at=issued_at,
        expires_at=access_token_expires_at,
    )
    refresh_token = create_refresh_token(
        data={**token_data, "jti": str(refresh_jti)},
        secret_key=settings.secret_key,
        issued_at=issued_at,
        expires_at=refresh_token_expires_at,
    )

    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/auth/verify-email", response_model=SuccessResponse)
async def verify_email(
    code: Annotated[str, Query()], db: Annotated[AsyncSession, Depends(get_db)]
):
    auth_entry = await get_user_by_verification_code(db, code)
    if not auth_entry:
        raise HTTPException(
            status_code=400, detail="Invalid or expired verification code"
        )

    await mark_email_as_verified(db, auth_entry.user_id)
    return SuccessResponse(message="Email successfully verified")


@router.post("/auth/refresh", response_model=TokenResponse)
async def refresh_access_token(
    request: RefreshTokenRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
):
    payload = decode_token(request.refresh_token, settings.secret_key)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )

    session_id = payload.get("sid")
    if not session_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token payload",
        )

    user_session = await get_active_session(db, uuid.UUID(session_id))
    if not user_session:
        # TODO: Может быть попытка взлома, необходимо уведомить пользователя
        raise HTTPException(status_code=401, detail="Session expired or reused")

    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    refresh_token_expires = timedelta(days=settings.refresh_token_expire_days)

    issued_at = datetime.now(timezone.utc)
    access_token_expires_at = issued_at + access_token_expires
    refresh_token_expires_at = issued_at + refresh_token_expires

    new_access_jti = uuid.uuid4()
    new_refresh_jti = uuid.uuid4()

    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    issued_at = datetime.now(timezone.utc)
    access_token_expires_at = issued_at + access_token_expires

    token_data = {
        "sub": str(user_session.user.id),
        "scopes": payload.get("scopes"),
        "sid": str(user_session.id),
    }
    access_token = create_access_token(
        data={**token_data, "jti": str(new_access_jti)},
        secret_key=settings.secret_key,
        issued_at=issued_at,
        expires_at=access_token_expires_at,
    )
    refresh_token = create_refresh_token(
        data={**token_data, "jti": str(new_refresh_jti)},
        secret_key=settings.secret_key,
        issued_at=issued_at,
        expires_at=refresh_token_expires_at,
    )

    await update_session_after_refresh(
        db,
        user_session,
        new_access_jti,
        new_refresh_jti,
        issued_at,
        refresh_token_expires_at,
    )

    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/auth/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    request_body: LogoutRequest,
    current_user_data: Annotated[TokenData, Depends(get_current_user_data)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    # TODO: Добавить в чёрный список

    if request_body.all_devices:
        await deactivate_all_user_sessions(db, current_user_data.sub)
    else:
        await deactivate_session(db, current_user_data.sid)

    return {}


@router.post("/auth/validate-token", response_model=TokenValidationResponse)
async def validate_token_internal(
    current_user_data: Annotated[TokenData, Depends(get_current_user_data)],
):
    return TokenValidationResponse(
        user_id=current_user_data.sub,
        scopes=current_user_data.scopes,
    )
