import logging
import json
from typing import Dict, List, Set
from fastapi import WebSocket
import redis.asyncio as redis

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        # Maps user_id -> List of active WebSockets
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, user_id: str, websocket: WebSocket, redis_client: redis.Redis):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)
        
        # Set Presence in Redis
        await redis_client.set(f"presence:{user_id}", "online", ex=300) # 5 min TTL
        logger.info(f"User {user_id} connected. Active devices: {len(self.active_connections[user_id])}")

    async def disconnect(self, user_id: str, websocket: WebSocket, redis_client: redis.Redis):
        if user_id in self.active_connections:
            if websocket in self.active_connections[user_id]:
                self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
                # Remove Presence
                await redis_client.delete(f"presence:{user_id}")
        logger.info(f"User {user_id} disconnected.")

    async def send_personal_message(self, user_id: str, message: dict):
        """Send a message to all devices of a specific user."""
        if user_id in self.active_connections:
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error sending to user {user_id}: {e}")

manager = ConnectionManager()
