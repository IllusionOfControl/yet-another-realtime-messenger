import uuid
from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user_data
from app.models import ChatType, MemberRole, ChatMember
from app.schemas import (
    ChatResponse, ChatShortResponse, GroupCreate, ChannelCreate, 
    ChatUpdate, ParticipantAdd, RoleUpdate, MembershipCheckResponse, TokenData
)
from app import crud
from app.services.kafka_producer import KafkaProducerService, get_kafka_producer

router = APIRouter(prefix="/api/v1")

@router.post("/chats/dm/{target_user_id}", response_model=ChatResponse)
async def get_or_create_dm(
    target_user_id: uuid.UUID,
    current_user: Annotated[TokenData, Depends(get_current_user_data)],
    db: Annotated[AsyncSession, Depends(get_db)],
    kafka: Annotated[KafkaProducerService, Depends(get_kafka_producer)]
):
    if target_user_id == current_user.sub:
        raise HTTPException(status_code=400, detail="Cannot create DM with yourself")
    chat = await crud.get_or_create_dm(db, current_user.sub, target_user_id)
    
    await kafka.publish_event("chat_created", {"chat_id": str(chat.id), "type": chat.type.value})
    return chat

@router.post("/chats/group", response_model=ChatResponse)
async def create_group(
    data: GroupCreate,
    current_user: Annotated[TokenData, Depends(get_current_user_data)],
    db: Annotated[AsyncSession, Depends(get_db)],
    kafka: Annotated[KafkaProducerService, Depends(get_kafka_producer)]
):
    settings = {"description": data.description, "is_public": False}
    chat = await crud.create_group_or_channel(db, current_user.sub, ChatType.GROUP, data.name, settings)
    
    await kafka.publish_event("chat_created", {"chat_id": str(chat.id), "type": chat.type.value})
    return chat

@router.post("/chats/channel", response_model=ChatResponse)
async def create_channel(
    data: ChannelCreate,
    current_user: Annotated[TokenData, Depends(get_current_user_data)],
    db: Annotated[AsyncSession, Depends(get_db)],
    kafka: Annotated[KafkaProducerService, Depends(get_kafka_producer)]
):
    settings = {"description": data.description, "is_public": data.is_public}
    chat = await crud.create_group_or_channel(db, current_user.sub, ChatType.CHANNEL, data.name, settings)
    
    await kafka.publish_event("chat_created", {"chat_id": str(chat.id), "type": chat.type.value})
    return chat

@router.get("/chats", response_model=List[ChatShortResponse])
async def list_my_chats(
    current_user: Annotated[TokenData, Depends(get_current_user_data)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    return await crud.get_user_chats(db, current_user.sub)

@router.get("/chats/{chat_id}", response_model=ChatResponse)
async def get_chat_details(
    chat_id: uuid.UUID,
    current_user: Annotated[TokenData, Depends(get_current_user_data)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    chat = await crud.get_chat_with_members(db, chat_id)
    if not chat: raise HTTPException(status_code=404)
    if not any(m.user_id == current_user.sub for m in chat.members):
        raise HTTPException(status_code=403, detail="Not a member")
    return chat

@router.put("/chats/{chat_id}", response_model=ChatResponse)
async def update_chat(
    chat_id: uuid.UUID,
    data: ChatUpdate,
    current_user: Annotated[TokenData, Depends(get_current_user_data)],
    db: Annotated[AsyncSession, Depends(get_db)],
    kafka: Annotated[KafkaProducerService, Depends(get_kafka_producer)]
):
    member = await crud.get_member(db, chat_id, current_user.sub)
    if not member or member.role not in [MemberRole.OWNER, MemberRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    chat = await crud.get_chat_with_members(db, chat_id)
    if not chat: raise HTTPException(status_code=404)
    
    if data.name: chat.name = data.name
    if data.description: chat.settings["description"] = data.description
    if data.is_public is not None: chat.settings["is_public"] = data.is_public
    
    await db.commit()
    await kafka.publish_event("chat_updated", {"chat_id": str(chat_id)})
    return chat

@router.post("/chats/{chat_id}/participants", status_code=201)
async def add_participant(
    chat_id: uuid.UUID,
    data: ParticipantAdd,
    current_user: Annotated[TokenData, Depends(get_current_user_data)],
    db: Annotated[AsyncSession, Depends(get_db)],
    kafka: Annotated[KafkaProducerService, Depends(get_kafka_producer)]
):
    member = await crud.get_member(db, chat_id, current_user.sub)
    if not member or member.role not in [MemberRole.OWNER, MemberRole.ADMIN]:
        raise HTTPException(status_code=403)
    
    new_member = ChatMember(chat_id=chat_id, user_id=data.user_id, role=MemberRole.MEMBER)
    db.add(new_member)
    await db.commit()
    
    await kafka.publish_event("participant_added", {"chat_id": str(chat_id), "user_id": str(data.user_id)})
    return {"status": "added"}

@router.delete("/chats/{chat_id}/participants/{user_id}")
async def remove_participant(
    chat_id: uuid.UUID,
    user_id: uuid.UUID,
    current_user: Annotated[TokenData, Depends(get_current_user_data)],
    db: Annotated[AsyncSession, Depends(get_db)],
    kafka: Annotated[KafkaProducerService, Depends(get_kafka_producer)]
):
    member = await crud.get_member(db, chat_id, current_user.sub)
    if not member or member.role not in [MemberRole.OWNER, MemberRole.ADMIN]:
        raise HTTPException(status_code=403)
    
    target = await crud.get_member(db, chat_id, user_id)
    if target:
        await db.delete(target)
        await db.commit()
        await kafka.publish_event("participant_removed", {"chat_id": str(chat_id), "user_id": str(user_id)})
    
    return status.HTTP_204_NO_CONTENT

@router.put("/chats/{chat_id}/participants/{user_id}/role")
async def update_role(
    chat_id: uuid.UUID,
    user_id: uuid.UUID,
    data: RoleUpdate,
    current_user: Annotated[TokenData, Depends(get_current_user_data)],
    db: Annotated[AsyncSession, Depends(get_db)],
    kafka: Annotated[KafkaProducerService, Depends(get_kafka_producer)]
):
    member = await crud.get_member(db, chat_id, current_user.sub)
    if not member or member.role != MemberRole.OWNER:
        raise HTTPException(status_code=403, detail="Only owner can change roles")
    
    target = await crud.get_member(db, chat_id, user_id)
    if not target: raise HTTPException(status_code=404)
    target.role = data.role
    await db.commit()
    
    await kafka.publish_event("role_updated", {"chat_id": str(chat_id), "user_id": str(user_id), "role": data.role.value})
    return {"status": "updated"}

@router.post("/chats/{chat_id}/leave")
async def leave_chat(
    chat_id: uuid.UUID,
    current_user: Annotated[TokenData, Depends(get_current_user_data)],
    db: Annotated[AsyncSession, Depends(get_db)],
    kafka: Annotated[KafkaProducerService, Depends(get_kafka_producer)]
):
    target = await crud.get_member(db, chat_id, current_user.sub)
    if target:
        if target.role == MemberRole.OWNER:
            raise HTTPException(status_code=400, detail="Owner cannot leave. Delete chat or transfer ownership.")
        await db.delete(target)
        await db.commit()
        await kafka.publish_event("participant_left", {"chat_id": str(chat_id), "user_id": str(current_user.sub)})
    return {"status": "left"}

@router.get("/channels/public/search", response_model=List[ChatShortResponse])
async def search_channels(
    query: str = Query(..., min_length=3),
    db: Annotated[AsyncSession, Depends(get_db)]
):
    return await crud.search_public_channels(db, query)

@router.get("/chats/{chat_id}/members/{user_id}/check", response_model=MembershipCheckResponse)
async def internal_check(chat_id: uuid.UUID, user_id: uuid.UUID, db: Annotated[AsyncSession, Depends(get_db)]):
    member = await crud.get_member(db, chat_id, user_id)
    if not member: return {"is_member": False}
    return {"is_member": True, "role": member.role}

@router.delete("/chats/{chat_id}")
async def delete_chat(
    chat_id: uuid.UUID,
    current_user: Annotated[TokenData, Depends(get_current_user_data)],
    db: Annotated[AsyncSession, Depends(get_db)],
    kafka: Annotated[KafkaProducerService, Depends(get_kafka_producer)]
):
    member = await crud.get_member(db, chat_id, current_user.sub)
    if not member or member.role != MemberRole.OWNER:
        raise HTTPException(status_code=403)
    await crud.delete_chat(db, chat_id)
    await kafka.publish_event("chat_deleted", {"chat_id": str(chat_id)})
    return status.HTTP_204_NO_CONTENT
