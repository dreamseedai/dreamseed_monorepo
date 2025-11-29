import json
import types

import pytest

import adaptive_engine.services.session_store_redis as ssr
from adaptive_engine import config as cfg


class FakeRedis:
    def __init__(self):
        self.store: dict[str, str] = {}
        self.ttl_map: dict[str, int] = {}
    def get(self, key: str):
        return self.store.get(key)
    def setex(self, key: str, ttl: int, value: str):
        # record ttl and value
        self.ttl_map[key] = int(ttl)
        self.store[key] = value
    def scan_iter(self, match: str):
        pre, suf = match.split("*")
        for k in list(self.store.keys()):
            if k.startswith(pre) and k.endswith(suf):
                yield k
    def delete(self, key: str):
        self.store.pop(key, None)
        self.ttl_map.pop(key, None)


def test_redis_session_store_roundtrip_and_prefix(monkeypatch):
    # Configure settings for prefix and TTL
    base = cfg.AppSettings(redis_key_prefix="adaptive:", session_ttl_sec=123, redis_url="redis://dev/0")
    # Patch both config and module-local get_settings inside session_store_redis
    monkeypatch.setattr(cfg, "get_settings", lambda: base, raising=True)
    monkeypatch.setattr(ssr, "get_settings", lambda: base, raising=True)

    fake = FakeRedis()
    # Patch redis module used inside session_store_redis
    monkeypatch.setattr(ssr, "redis", types.SimpleNamespace(Redis=types.SimpleNamespace(from_url=lambda *a, **k: fake)), raising=True)

    store = ssr.RedisSessionStore()
    # Create a session and ensure it was saved with setex, correct prefix, and ttl
    st = store.create_session(user_id=1, exam_id=2, time_limit_sec=60)
    key = f"{base.redis_key_prefix}sess:{st.session_id}"
    assert key in fake.store
    assert fake.ttl_map[key] == 123

    # Load it back
    st2 = store.get(st.session_id)
    assert st2 is not None
    assert st2.session_id == st.session_id
    assert st2.user_id == 1 and st2.exam_id == 2

    # Update something and save()
    st2.remaining_time_sec = 55
    store.save(st2)
    # Value should be JSON with updated remaining_time_sec
    obj = json.loads(fake.store[key])
    assert obj.get("remaining_time_sec") == 55

    # clear_all should delete keys with prefix
    store.clear_all()
    assert key not in fake.store
