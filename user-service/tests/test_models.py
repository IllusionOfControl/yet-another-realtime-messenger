import uuid

from app.models import ContactStatus, UserContact, UserProfile


def test_user_profile_model():
    user_id = uuid.uuid4()
    profile = UserProfile(id=user_id, username="testuser", is_active=True)
    assert profile.id == user_id
    assert profile.username == "testuser"
    assert profile.display_name is None
    assert profile.is_active


def test_user_contact_model():
    owner_id = uuid.uuid4()
    contact_id = uuid.uuid4()
    contact = UserContact(
        owner_id=owner_id, contact_user_id=contact_id, status=ContactStatus.FRIEND
    )
    assert contact.owner_id == owner_id
    assert contact.contact_user_id == contact_id
    assert contact.status == ContactStatus.FRIEND
