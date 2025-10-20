import json
import os
import time
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
	"""Validate and publish an event with ordering by org_id.
	Returns message_id on success, raises on failure.
	"""
	validate_event(event, schema_path)
	ordering_key = str(event["payload"]["org_id"])  # org-level ordering
	data = json.dumps(event, ensure_ascii=False).encode("utf-8")

	backoff = 0.5
	for attempt in range(1, max_retries + 1):
		future = publisher.publish(topic_path, data=data, ordering_key=ordering_key)
		try:
			message_id = future.result(timeout=10)
			return message_id
		except Exception:
			if attempt == max_retries:
				raise
			time.sleep(backoff)
			backoff = min(backoff * 2 * 1.1, 5.0)
	return ""  # unreachable
