import json
import logging
from typing import Optional

from aiokafka import AIOKafkaProducer

from app.settings import Settings, get_settings

logger = logging.getLogger(__name__)


class KafkaProducerService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.producer: Optional[AIOKafkaProducer] = None

    async def start(self):
        if not self.producer:
            self.producer = AIOKafkaProducer(
                bootstrap_servers=self.settings.kafka_bootstrap_servers
            )
            await self.producer.start()
            logger.info("Kafka Producer started")

    async def stop(self):
        if self.producer:
            await self.producer.stop()
            logger.info("Kafka Producer stopped")

    async def publish_event(self, event_type: str, data: dict):
        if not self.producer:
            await self.start()

        payload = {"event_type": event_type, "data": data}
        await self.producer.send_and_wait(
            self.settings.kafka_topic_chats,
            json.dumps(payload, default=str).encode("utf-8"),
        )


producer_service = KafkaProducerService(get_settings())


async def get_kafka_producer() -> KafkaProducerService:
    return producer_service
