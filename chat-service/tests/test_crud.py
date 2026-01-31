import uuid
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app import crud
from app.models import ChatType, MemberRole

@pytest.mark.asyncio
async def test_get_or_create_dm(db_session: AsyncSession):
    user_a = uuid.uuid4()
    user_b = uuid.uuid4()
    
    chat = await crud.get_or_create_dm(db_session, user_a, user_b)
    assert chat.type == ChatType.DM
    assert len(chat.members) == 2
    
    chat2 = await crud.get_or_create_dm(db_session, user_a, user_b)
    assert chat.id == chat2.id

@pytest.mark.asyncio
async def test_create_group_and_get_user_chats(db_session: AsyncSession):
    creator_id = uuid.uuid4()
    chat_name = "Team Alpha"
    settings = {"description": "Top secret"}
    
    chat = await crud.create_group_or_channel(
        db_session, creator_id, ChatType.GROUP, chat_name, settings
    )
    assert chat.name == chat_name
    assert chat.members[0].user_id == creator_id
    assert chat.members[0].role == MemberRole.OWNER
    
    user_chats = await crud.get_user_chats(db_session, creator_id)
    assert len(user_chats) == 1
    assert user_chats[0].id == chat.id

@pytest.mark.asyncio
async def test_search_public_channels(db_session: AsyncSession):
    creator_id = uuid.uuid4()
    
    await crud.create_group_or_channel(
        db_session, creator_id, ChatType.CHANNEL, "Public News", {"is_public": "true"}
    )
    await crud.create_group_or_channel(
        db_session, creator_id, ChatType.CHANNEL, "Private Secrets", {"is_public": "false"}
    )
    
    results = await crud.search_public_channels(db_session, "News")
    assert len(results) == 1
    assert results[0].name == "Public News"

@pytest.mark.asyncio
async def test_member_and_delete_operations(db_session: AsyncSession):
    user_id = uuid.uuid4()
    chat = await crud.create_group_or_channel(
        db_session, user_id, ChatType.GROUP, "Delete Me", {}
    )
    
    member = await crud.get_member(db_session, chat.id, user_id)
    assert member is not None
    assert member.role == MemberRole.OWNER
    
    await crud.delete_chat(db_session, chat.id)
    deleted_chat = await crud.get_chat_with_members(db_session, chat.id)
    assert deleted_chat is None
