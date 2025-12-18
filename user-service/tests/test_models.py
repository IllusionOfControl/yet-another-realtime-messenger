import uuid

from app.models import ContactStatus


def test_user_profile_model(user_profile_factory):
    user_id = uuid.uuid4()
    username= "testuser"
    display_name = "test user"
    email = "testemail@example.com"
    profile = user_profile_factory(id=user_id, username=username, email=email, display_name=display_name)
    assert profile.id == user_id
    assert profile.username == username
    assert profile.display_name == display_name
    assert profile.email == email


def test_user_contact_model(user_contact_factory):
    owner_id = uuid.uuid4()
    contact_id = uuid.uuid4()
    contact_status = ContactStatus.FRIEND
    contact = user_contact_factory(owner_id=owner_id, contact_id=contact_id, status=contact_status)
    assert contact.owner_id == owner_id
    assert contact.contact_id == contact_id
    assert contact.status == contact_status
