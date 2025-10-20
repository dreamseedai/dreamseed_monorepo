import json
import os
import time
import random
import logging
from typing import Dict
from google.cloud import pubsub_v1
from .validator import validate_event

PROJECT_ID = os.getenv("PROJECT_ID", "dreamseedai-prod")
TOPIC_ID = os.getenv("PUBSUB_TOPIC_EVENTS", "seedtest-events")

# Enable message ordering
publisher_options = pubsub_v1.types.PublisherOptions(enable_message_ordering=True)
publisher = pubsub_v1.PublisherClient(publisher_options=publisher_options)
topic_path = publisher.topic_path(PROJECT_ID, TOPIC_ID)


def publish_event(event: Dict, schema_path: str, max_retries: int = 3) -> str:
    """Validate and publish an event with ordering by session/attempt/org.
    Returns message_id on success, raises on failure.
    """
    validate_event(event, schema_path)
    payload = event.get("payload", {})
    ordering_key = str(
        payload.get("session_id")
        or payload.get("attempt_id")
        or payload.get("org_id")
    )
    data = json.dumps(event, ensure_ascii=False).encode("utf-8")

    backoff = 0.5
    start = time.monotonic()
    for attempt in range(1, max_retries + 1):
        future = publisher.publish(topic_path, data=data, ordering_key=ordering_key)
        try:
            message_id = future.result(timeout=10)
            elapsed_ms = int((time.monotonic() - start) * 1000)
            logging.info(
                "pubsub_publish_success topic=%s ordering_key=%s attempt=%d elapsed_ms=%d msg_id=%s",
                TOPIC_ID,
                ordering_key,
                attempt,
                elapsed_ms,
                message_id,
            )
            return message_id
        except Exception as e:
            if attempt == max_retries:
                logging.error(
                    "pubsub_publish_failed topic=%s ordering_key=%s attempt=%d error=%s",
                    TOPIC_ID,
                    ordering_key,
                    attempt,
                    repr(e),
                )
                raise
            # jittered exponential backoff
            jitter = backoff * (0.9 + 0.2 * random.random())
            time.sleep(jitter)
            backoff = min(backoff * 2, 5.0)
    return ""  # unreachable
