import uuid

import pytest

from app.models import Chat, ChatMember, ChatType, MemberRole


def test_chat_model_creation():
    chat_id = uuid.uuid4()
    chat = Chat(
        id=chat_id, type=ChatType.GROUP, name="Project X", settings={"is_public": False}
    )
    assert chat.id == chat_id
    assert chat.type == ChatType.GROUP
    assert chat.name == "Project X"
    assert chat.settings["is_public"] is False


def test_chat_member_model_creation():
    member_id = uuid.uuid4()
    chat_id = uuid.uuid4()
    user_id = uuid.uuid4()
    member = ChatMember(
        id=member_id, chat_id=chat_id, user_id=user_id, role=MemberRole.ADMIN
    )
    assert member.id == member_id
    assert member.chat_id == chat_id
    assert member.user_id == user_id
    assert member.role == MemberRole.ADMIN


def test_chat_repr():
    chat = Chat(type=ChatType.DM, name=None)
    assert "DM" in repr(chat)


def test_chat_member_repr():
    member = ChatMember(user_id=uuid.uuid4(), role=MemberRole.OWNER)
    assert "OWNER" in repr(member)
