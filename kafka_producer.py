
import os
import json
import asyncio
from aiokafka import AIOKafkaProducer

async def main():
    brokers = os.getenv("KAFKA_BROKERS", "localhost:9092")
    topic = os.getenv("KAFKA_TOPIC", "security-events")
    producer = AIOKafkaProducer(
        bootstrap_servers=brokers,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )
    await producer.start()
    try:
        sample = {
            "timestamp": "2025-08-09T12:00:00Z",
            "source": "web-firewall",
            "ip": "203.0.113.5",
            "message": "Multiple failed logins detected; possible brute force",
            "severity": "Warn"
        }
        await producer.send_and_wait(topic, sample)
        print("Sent sample event to", topic)
    finally:
        await producer.stop()

if __name__ == "__main__":
    asyncio.run(main())
