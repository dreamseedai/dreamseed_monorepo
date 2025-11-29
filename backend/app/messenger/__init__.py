"""
Messenger package

Real-time messaging system for DreamSeed AI platform.

Modules:
- pubsub: Redis Pub/Sub manager for message broadcasting
- websocket: WebSocket connection manager (TODO)
- events: WebSocket event handlers (TODO)
"""

from app.messenger.pubsub import MessengerPubSub, get_pubsub

__all__ = ["MessengerPubSub", "get_pubsub"]
