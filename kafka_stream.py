
import os
import json
import asyncio
from typing import Optional

from aiokafka import AIOKafkaConsumer
from models import LogEvent

DEFAULT_TOPIC = os.getenv("KAFKA_TOPIC", "security-events")

async def start_kafka_consumer(loop, event_queue: asyncio.Queue):
    brokers = os.getenv("KAFKA_BROKERS")
    if not brokers:
        return None  # Kafka disabled

    group_id = os.getenv("KAFKA_GROUP_ID", "rtg-consumer")
    consumer = AIOKafkaConsumer(
        DEFAULT_TOPIC,
        loop=loop,
        bootstrap_servers=brokers,
        group_id=group_id,
        enable_auto_commit=True,
        value_deserializer=lambda v: v.decode("utf-8"),
        auto_offset_reset=os.getenv("KAFKA_AUTO_OFFSET_RESET", "earliest"),
    )
    await consumer.start()

    async def _consume():
        try:
            async for msg in consumer:
                try:
                    data = json.loads(msg.value)
                    event = LogEvent.model_validate(data)
                    event_queue.put_nowait(event)
                except Exception:
                    # drop malformed
                    pass
        finally:
            await consumer.stop()

    task = asyncio.create_task(_consume())
    return task
