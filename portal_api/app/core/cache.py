from __future__ import annotations

import hashlib
import json
from functools import lru_cache
from typing import Any, Awaitable, Callable, Optional

import redis.asyncio as redis  # type: ignore
from app.core.config import get_settings


@lru_cache
def _client() -> Optional["redis.Redis"]:
    url = get_settings().redis_url
    if not url:
        return None
    return redis.from_url(url, decode_responses=True)


def _key(prefix: str, **params) -> str:
    payload = json.dumps(params, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha1(payload.encode()).hexdigest()
    return f"{prefix}:{digest}"


async def get_or_set(prefix: str, maker: Callable[[], Awaitable[Any]], ttl: Optional[int] = None, **params) -> Any:
    r = _client()
    if not r:
        return await maker()
    k = _key(prefix, **params)
    val = await r.get(k)  # type: ignore[attr-defined]
    if val is not None:
        return json.loads(val)
    data = await maker()
    await r.set(k, json.dumps(data), ex=ttl or get_settings().cache_ttl_seconds)  # type: ignore[attr-defined]
    return data


async def delete_prefix(prefix: str):
    r = _client()
    if not r:
        return
    async for key in r.scan_iter(match=f"{prefix}:*"):  # type: ignore[attr-defined]
        await r.delete(key)  # type: ignore[attr-defined]


