from __future__ import annotations

import time
from functools import lru_cache
from typing import Optional

import redis.asyncio as redis  # type: ignore
from app.core.config import get_settings


@lru_cache
def _r() -> Optional["redis.Redis"]:
    url = get_settings().redis_url
    if not url:
        return None
    return redis.from_url(url, decode_responses=True)


async def check_rate_limit(bucket: str, limit: int, period_sec: int = 60) -> bool:
    """
    Returns True if allowed, False if over limit.
    """
    r = _r()
    if not r:
        return True
    key = f"rl:{bucket}"
    pipe = r.pipeline()
    now = int(time.time())
    pipe.incr(key)  # type: ignore[attr-defined]
    pipe.expire(key, period_sec)  # type: ignore[attr-defined]
    cnt, _ = await pipe.execute()  # type: ignore[attr-defined]
    return int(cnt) <= limit
