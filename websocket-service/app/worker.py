import json
import logging
import asyncio
from aiokafka import AIOKafkaConsumer
from app.settings import get_settings
from app.manager import manager

logger = logging.getLogger(__name__)

async def kafka_worker():
    settings = get_settings()
    consumer = AIOKafkaConsumer(
        settings.kafka_message_topic,
        bootstrap_servers=settings.kafka_bootstrap_servers,
        group_id=f"websocket_service_{settings.app_host}", # Unique per instance
        auto_offset_reset="latest"
    )
    
    await consumer.start()
    logger.info("Kafka Message Consumer started")
    
    try:
        async for msg in consumer:
            try:
                data = json.loads(msg.value.decode("utf-8"))
                # Expected payload: {"type": "new_message", "recipients": ["uuid1", "uuid2"], "payload": {...}}
                recipients = data.get("recipients", [])
                message_payload = {
                    "type": data.get("type", "message"),
                    "data": data.get("payload")
                }
                
                # Push to all local recipients
                for user_id in recipients:
                    await manager.send_personal_message(user_id, message_payload)
                    
            except Exception as e:
                logger.error(f"Worker error: {e}")
    finally:
        await consumer.stop()
        logger.info("Kafka Message Consumer stopped")
