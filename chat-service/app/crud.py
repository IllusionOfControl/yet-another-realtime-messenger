import uuid
from typing import List, Optional

from sqlalchemy import and_, delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Chat, ChatMember, ChatType, MemberRole


async def get_or_create_dm(
    db: AsyncSession, user_a: uuid.UUID, user_b: uuid.UUID
) -> Chat:
    stmt = (
        select(Chat)
        .join(ChatMember)
        .where(Chat.type == ChatType.DM)
        .where(ChatMember.user_id.in_([user_a, user_b]))
        .group_by(Chat.id)
        .having(func.count(ChatMember.user_id) == 2)
    )
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()

    if existing:
        return await get_chat_with_members(db, existing.id)

    new_chat = Chat(type=ChatType.DM, settings={})
    db.add(new_chat)
    await db.flush()

    db.add(ChatMember(chat_id=new_chat.id, user_id=user_a, role=MemberRole.MEMBER))
    db.add(ChatMember(chat_id=new_chat.id, user_id=user_b, role=MemberRole.MEMBER))

    await db.commit()
    return await get_chat_with_members(db, new_chat.id)


async def create_group_or_channel(
    db: AsyncSession,
    creator_id: uuid.UUID,
    chat_type: ChatType,
    name: str,
    settings: dict,
) -> Chat:
    new_chat = Chat(type=chat_type, name=name, settings=settings)
    db.add(new_chat)
    await db.flush()

    owner = ChatMember(chat_id=new_chat.id, user_id=creator_id, role=MemberRole.OWNER)
    db.add(owner)

    await db.commit()
    return await get_chat_with_members(db, new_chat.id)


async def get_user_chats(db: AsyncSession, user_id: uuid.UUID) -> List[Chat]:
    stmt = (
        select(Chat)
        .join(ChatMember)
        .where(ChatMember.user_id == user_id)
        .order_by(Chat.created_at.desc())
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_chat_with_members(db: AsyncSession, chat_id: uuid.UUID) -> Optional[Chat]:
    stmt = select(Chat).options(selectinload(Chat.members)).where(Chat.id == chat_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def search_public_channels(db: AsyncSession, query: str) -> List[Chat]:
    stmt = (
        select(Chat)
        .where(Chat.type == ChatType.CHANNEL)
        .where(Chat.settings["is_public"].as_boolean() == True)
        .where(Chat.name.ilike(f"%{query}%"))
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_member(
    db: AsyncSession, chat_id: uuid.UUID, user_id: uuid.UUID
) -> Optional[ChatMember]:
    stmt = select(ChatMember).where(
        ChatMember.chat_id == chat_id, ChatMember.user_id == user_id
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def delete_chat(db: AsyncSession, chat_id: uuid.UUID):
    await db.execute(delete(Chat).where(Chat.id == chat_id))
    await db.commit()
