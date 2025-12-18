import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import (
    add_or_update_contact,
    create_user_profile,
    get_user_contacts,
    get_user_profile_by_email,
    get_user_profile_by_id,
    get_user_profile_by_username,
    remove_contact_entry,
    search_user_profiles,
    update_user_avatar,
    update_user_profile,
)
from app.database import get_db
from app.dependencies import get_current_user_id
from app.models import ContactStatus
from app.schemas import (
    ContactResponse,
    SearchParams,
    UserProfileCreate,
    UserProfileResponse,
    UserProfileUpdate,
    UserSearchResult,
)
from app.services.file_upload_client import FileUploadClient, get_file_upload_client

router = APIRouter(prefix="/api/v1")


@router.post("/ping")
async def ping():
    return "pong"


@router.post(
    "/users/internal/create-profile",
    response_model=UserProfileResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_user_profile_internal(
    user_profile_create: UserProfileCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    if await get_user_profile_by_username(db, user_profile_create.username):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Username already exists"
        )
    if await get_user_profile_by_email(db, user_profile_create.username):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with email already exists",
        )

    user_profile = await create_user_profile(db, user_profile_create)
    return UserProfileResponse(
        id=user_profile.id,
        username=user_profile.username,
        display_name=user_profile.display_name,
        email=user_profile.email,
        bio=user_profile.bio,
        custom_status=user_profile.custom_status,
        created_at=user_profile.created_at,
        updated_at=user_profile.updated_at,
    )


@router.get("/users/search", response_model=list[UserSearchResult])
async def search_users(
    search_query: Annotated[SearchParams, Query()],
    db: Annotated[AsyncSession, Depends(get_db)],
    file_upload_client: Annotated[FileUploadClient, Depends(get_file_upload_client)],
):
    user_profiles = await search_user_profiles(
        db, search_query.query, search_query.limit, search_query.offset
    )

    results = []
    for profile in user_profiles:
        avatar_url = None
        if profile.avatar_file_id:
            avatar_url = await file_upload_client.get_signed_url(
                profile.avatar_file_id, thumbnail=True
            )
        results.append(
            UserSearchResult(
                id=profile.id,
                username=profile.username,
                display_name=profile.display_name,
                avatar_url=avatar_url,
            )
        )
    return results


@router.get(path="/users/me", response_model=UserProfileResponse)
async def read_users_me(
    current_user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
    file_upload_client: Annotated[FileUploadClient, Depends(get_file_upload_client)],
):
    user_profile = await get_user_profile_by_id(db, current_user_id)
    if not user_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User profile not found"
        )

    avatar_url = None
    if user_profile.avatar_file_id:
        avatar_url = await file_upload_client.get_signed_url(
            user_profile.avatar_file_id, thumbnail=True
        )

    return UserProfileResponse(
        id=user_profile.id,
        username=user_profile.username,
        display_name=user_profile.display_name,
        email=user_profile.email,
        bio=user_profile.bio,
        custom_status=user_profile.custom_status,
        avatar_url=avatar_url,
        created_at=user_profile.created_at,
        updated_at=user_profile.updated_at,
    )


@router.put(path="/users/me", response_model=UserProfileResponse)
async def update_users_me(
    user_profile_update: UserProfileUpdate,
    current_user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
    file_upload_client: Annotated[FileUploadClient, Depends(get_file_upload_client)],
):
    updated_profile = await update_user_profile(
        db, current_user_id, user_profile_update
    )
    if not updated_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User profile not found"
        )

    avatar_url = None
    if updated_profile.avatar_file_id:
        avatar_url = await file_upload_client.get_signed_url(
            updated_profile.avatar_file_id, thumbnail=True
        )

    return UserProfileResponse(
        id=updated_profile.id,
        username=updated_profile.username,
        display_name=updated_profile.display_name,
        email=updated_profile.email,
        bio=updated_profile.bio,
        custom_status=updated_profile.custom_status,
        avatar_url=avatar_url,
        created_at=updated_profile.created_at,
        updated_at=updated_profile.updated_at,
    )


@router.post("/users/me/avatar", response_model=UserProfileResponse)
async def upload_user_avatar(
    current_user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
    file: Annotated[UploadFile, File(...)],
    file_upload_client: Annotated[FileUploadClient, Depends(get_file_upload_client)],
):
    auth_header = "Bearer some_internal_or_forwarded_token"

    file_content = await file.read()
    uploaded_file_info = await file_upload_client.upload_file(
        file_content, file.filename, file.content_type, auth_header
    )

    if not uploaded_file_info:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload avatar file",
        )

    file_id = uploaded_file_info["id"]
    updated_profile = await update_user_avatar(db, current_user_id, uuid.UUID(file_id))
    if not updated_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found after avatar update",
        )

    avatar_url = await file_upload_client.get_signed_url(
        updated_profile.avatar_file_id, thumbnail=True
    )
    return UserProfileResponse(
        id=updated_profile.id,
        username=updated_profile.username,
        display_name=updated_profile.display_name,
        email=updated_profile.email,
        bio=updated_profile.bio,
        custom_status=updated_profile.custom_status,
        avatar_url=avatar_url,
        created_at=updated_profile.created_at,
        updated_at=updated_profile.updated_at,
    )


@router.get("/users/{user_id}", response_model=UserProfileResponse)
async def read_user_profile(
    user_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    file_upload_client: Annotated[FileUploadClient, Depends(get_file_upload_client)],
):
    user_profile = await get_user_profile_by_id(db, user_id)
    if not user_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User profile not found"
        )

    avatar_url = None
    if user_profile.avatar_file_id:
        avatar_url = await file_upload_client.get_signed_url(
            user_profile.avatar_file_id, thumbnail=True
        )

    return UserProfileResponse(
        id=user_profile.id,
        username=user_profile.username,
        display_name=user_profile.display_name,
        email=user_profile.email,
        bio=user_profile.bio,
        custom_status=user_profile.custom_status,
        avatar_url=avatar_url,
        created_at=user_profile.created_at,
        updated_at=user_profile.updated_at,
    )


@router.post(
    "/users/me/contacts/{contact_id}/friend", response_model=ContactResponse
)
async def add_friend(
    contact_id: uuid.UUID,
    current_user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
    file_upload_client: Annotated[FileUploadClient, Depends(get_file_upload_client)],
):
    if current_user_id == contact_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot add yourself as a friend",
        )

    contact_profile = await get_user_profile_by_id(db, contact_id)
    if not contact_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Contact user not found"
        )

    contact_entry = await add_or_update_contact(
        db, current_user_id, contact_id, ContactStatus.FRIEND
    )

    avatar_url = None
    if contact_profile.avatar_file_id:
        avatar_url = await file_upload_client.get_signed_url(
            contact_profile.avatar_file_id, thumbnail=True
        )

    return ContactResponse(
        id=contact_entry.id,
        contact_id=contact_entry.contact_id,
        status=contact_entry.status,
        username=contact_profile.username,
        display_name=contact_profile.display_name,
        avatar_url=avatar_url,
    )


@router.post(
    "/users/me/contacts/{contact_id}/block", response_model=ContactResponse
)
async def block_user(
    contact_id: uuid.UUID,
    current_user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
    file_upload_client: Annotated[FileUploadClient, Depends(get_file_upload_client)],
):
    if current_user_id == contact_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot block yourself"
        )

    contact_profile = await get_user_profile_by_id(db, contact_id)
    if not contact_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User to block not found"
        )

    contact_entry = await add_or_update_contact(
        db, current_user_id, contact_id, ContactStatus.BLOCKED
    )

    avatar_url = None
    if contact_profile.avatar_file_id:
        avatar_url = await file_upload_client.get_signed_url(
            contact_profile.avatar_file_id, thumbnail=True
        )

    return ContactResponse(
        id=contact_entry.id,
        contact_id=contact_entry.contact_id,
        status=contact_entry.status,
        username=contact_profile.username,
        display_name=contact_profile.display_name,
        avatar_url=avatar_url,
    )


@router.delete(
    "/users/me/contacts/{contact_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def remove_contact(
    contact_id: uuid.UUID,
    current_user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
    file_upload_client: Annotated[FileUploadClient, Depends(get_file_upload_client)],
):
    success = await remove_contact_entry(db, current_user_id, contact_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found"
        )
    return


@router.get("/users/me/contacts", response_model=list[ContactResponse])
async def get_my_contacts(
    current_user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
    file_upload_client: Annotated[FileUploadClient, Depends(get_file_upload_client)],
):
    user_contacts = await get_user_contacts(db, current_user_id)
    results = []
    for contact_entry in user_contacts:
        contact_profile = await get_user_profile_by_id(
            db, contact_entry.contact_id
        )
        if not contact_profile:
            continue  # Should not happen if data integrity is maintained

        avatar_url = None
        if contact_profile.avatar_file_id:
            avatar_url = await file_upload_client.get_signed_url(
                contact_profile.avatar_file_id, thumbnail=True
            )

        results.append(
            ContactResponse(
                id=contact_entry.id,
                contact_id=contact_entry.contact_id,
                status=contact_entry.status,
                username=contact_profile.username,
                display_name=contact_profile.display_name,
                avatar_url=avatar_url,
            )
        )
    return results
