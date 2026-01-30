import logging
import asyncio
import jwt
from typing import Optional
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query, Depends
from app.settings import get_settings, Settings
from app.manager import manager
from app.worker import kafka_worker
from app.logger import configure_logging
import redis.asyncio as redis

logger = logging.getLogger(__name__)

async def get_redis():
    settings = get_settings()
    client = redis.from_url(settings.redis_url, decode_responses=True)
    try:
        yield client
    finally:
        await client.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start Kafka background worker
    worker_task = asyncio.create_task(kafka_worker())
    logger.info("WebSocket Service startup...")
    yield
    worker_task.cancel()
    try:
        await worker_task
    except asyncio.CancelledError:
        logger.info("Kafka worker task cancelled")
    logger.info("WebSocket Service shutdown...")

def get_app():
    settings = get_settings()
    configure_logging(settings.log_level, settings.log_format)
    
    app = FastAPI(title="WebSocket Service", lifespan=lifespan)
    
    def validate_token(token: str) -> Optional[str]:
        settings = get_settings()
        try:
            # Note: We use public_key for RS256 validation as per auth-service
            payload = jwt.decode(token, settings.public_key, algorithms=["RS256"])
            return payload.get("sub")
        except Exception as e:
            logger.debug(f"Token validation failed: {e}")
            return None

    @app.websocket("/ws")
    async def websocket_endpoint(
        websocket: WebSocket,
        token: str = Query(...),
        redis_client: redis.Redis = Depends(get_redis)
    ):
        user_id = validate_token(token)
        if not user_id:
            await websocket.close(code=1008) # Policy Violation
            return

        await manager.connect(user_id, websocket, redis_client)
        
        try:
            while True:
                # Keep connection alive and handle incoming client signals
                data = await websocket.receive_text()
                # Process signals if needed
        except WebSocketDisconnect:
            await manager.disconnect(user_id, websocket, redis_client)
        except Exception as e:
            logger.error(f"WS Error for user {user_id}: {e}")
            await manager.disconnect(user_id, websocket, redis_client)

    return app

app = get_app()
