import uuid
import pytest
from app.models import ChatType, MemberRole

@pytest.mark.asyncio
async def test_create_dm_flow(client, current_user_id, mock_kafka_producer):
    target_user_id = uuid.uuid4()
    
    resp = await client.post(f"/api/v1/chats/dm/{target_user_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["type"] == "DM"
    assert len(data["members"]) == 2
    
    mock_kafka_producer.publish_event.assert_called_with(
        "chat_created", {"chat_id": data["id"], "type": "DM"}
    )
    
    resp2 = await client.post(f"/api/v1/chats/dm/{target_user_id}")
    assert resp2.status_code == 200
    assert resp2.json()["id"] == data["id"]

@pytest.mark.asyncio
async def test_group_chat_management(client, current_user_id):
    group_data = {"name": "Test Group", "description": "A test group chat"}
    resp = await client.post("/api/v1/chats/group", json=group_data)
    assert resp.status_code == 200
    chat_id = resp.json()["id"]
    
    new_user_id = str(uuid.uuid4())
    add_resp = await client.post(
        f"/api/v1/chats/{chat_id}/participants", 
        json={"user_id": new_user_id}
    )
    assert add_resp.status_code == 201
    
    details_resp = await client.get(f"/api/v1/chats/{chat_id}")
    assert details_resp.status_code == 200
    members = details_resp.json()["members"]
    assert any(m["user_id"] == str(current_user_id) and m["role"] == "OWNER" for m in members)
    assert any(m["user_id"] == new_user_id and m["role"] == "MEMBER" for m in members)
    
    update_resp = await client.put(
        f"/api/v1/chats/{chat_id}",
        json={"name": "Updated Name", "description": "New description"}
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["name"] == "Updated Name"

@pytest.mark.asyncio
async def test_channel_search(client):
    channel_data = {"name": "Public News", "description": "Global news", "is_public": True}
    await client.post("/api/v1/chats/channel", json=channel_data)
    
    search_resp = await client.get("/api/v1/channels/public/search", params={"query": "News"})
    assert search_resp.status_code == 200
    results = search_resp.json()
    assert len(results) >= 1
    assert any("News" in c["name"] for c in results)

@pytest.mark.asyncio
async def test_leave_and_delete_chat(client, current_user_id):
    resp = await client.post("/api/v1/chats/group", json={"name": "Temp Group"})
    chat_id = resp.json()["id"]
    
    leave_resp = await client.post(f"/api/v1/chats/{chat_id}/leave")
    assert leave_resp.status_code == 400
    assert "Owner cannot leave" in leave_resp.json()["detail"]
    
    del_resp = await client.delete(f"/api/v1/chats/{chat_id}")
    assert del_resp.status_code == 204
    
    get_resp = await client.get(f"/api/v1/chats/{chat_id}")
    assert get_resp.status_code == 404
