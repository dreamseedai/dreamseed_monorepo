from __future__ import annotations

import json
import logging
import threading
import time
from typing import Any, Callable, Optional

try:
    import redis  # type: ignore
except Exception:  # pragma: no cover - redis is optional
    redis = None  # type: ignore

from ..settings import settings

log = logging.getLogger(__name__)


class LocalTTLCache:
    """Simple in-process TTL cache.

    Not shared across processes/containers. Used as fallback when Redis is not configured or unavailable.
    """

    def __init__(self) -> None:
        self._store: dict[str, tuple[float, Any, int]] = {}
        self._lock = threading.Lock()

    def get_json(self, key: str) -> Any | None:
        now = time.time()
        with self._lock:
            entry = self._store.get(key)
            if not entry:
                return None
            ts, value, ttl = entry
            if now - ts >= ttl:
                # expired
                self._store.pop(key, None)
                return None
            return value

    def set_json(self, key: str, value: Any, ttl: int) -> None:
        with self._lock:
            self._store[key] = (time.time(), value, int(ttl))

    def delete(self, key: str) -> None:
        with self._lock:
            self._store.pop(key, None)

    def delete_prefix(self, prefix: str) -> int:
        with self._lock:
            keys = [k for k in self._store.keys() if k.startswith(prefix)]
            for k in keys:
                self._store.pop(k, None)
            return len(keys)


class RedisJsonCache:
    """Redis-backed JSON cache with best-effort connectivity and short timeouts."""

    def __init__(self, url: str, prefix: str = "", socket_timeout: float = 0.3, connect_timeout: float = 0.3) -> None:
        if redis is None:
            raise RuntimeError("redis package not installed")
        self._prefix = prefix or ""
        self._client = redis.Redis.from_url(
            url,
            decode_responses=True,
            socket_timeout=socket_timeout,
            socket_connect_timeout=connect_timeout,
            health_check_interval=30,
        )
        # Probe connectivity quickly; if fails, we'll let caller decide to fallback
        try:
            self._client.ping()
        except Exception as e:
            raise RuntimeError(f"Redis not reachable: {e}")

    def _k(self, key: str) -> str:
        return f"{self._prefix}{key}"

    def get_json(self, key: str) -> Any | None:
        try:
            from typing import Optional, cast
            raw = cast(Optional[str], self._client.get(self._k(key)))
            if raw is None:
                return None
            return json.loads(raw)
        except Exception as e:  # pragma: no cover - I/O protection
            log.debug("Redis get_json failed for %s: %s", key, e)
            return None

    def set_json(self, key: str, value: Any, ttl: int) -> None:
        try:
            raw = json.dumps(value, separators=(",", ":"))
            self._client.setex(self._k(key), int(ttl), raw)
        except Exception as e:  # pragma: no cover - I/O protection
            log.debug("Redis set_json failed for %s: %s", key, e)

    def delete(self, key: str) -> None:
        try:
            self._client.delete(self._k(key))
        except Exception as e:  # pragma: no cover
            log.debug("Redis delete failed for %s: %s", key, e)

    def delete_prefix(self, prefix: str) -> int:
        """Delete keys with the given logical prefix. Returns count best-effort.

        Uses SCAN to avoid blocking Redis. Falls back silently on errors.
        """
        try:
            full_prefix = self._k(prefix)
            pattern = full_prefix + "*"
            total = 0
            # Use scan_iter with small count hint to avoid blocking
            for k in self._client.scan_iter(match=pattern, count=100):
                try:
                    self._client.delete(k)
                    total += 1
                except Exception:
                    pass
            return total
        except Exception as e:  # pragma: no cover
            log.debug("Redis delete_prefix failed for %s: %s", prefix, e)
            return 0


class HybridCache:
    """Layered cache: prefer Redis when configured/available, else fall back to local TTL."""

    def __init__(self, primary: Optional[RedisJsonCache], fallback: LocalTTLCache) -> None:
        self._primary = primary
        self._fallback = fallback

    def get_json(self, key: str) -> Any | None:
        # Try Redis first
        if self._primary is not None:
            val = self._primary.get_json(key)
            if val is not None:
                return val
        # Fallback
        return self._fallback.get_json(key)

    def set_json(self, key: str, value: Any, ttl: int) -> None:
        # Write-through to both layers; ignore errors in primary
        if self._primary is not None:
            try:
                self._primary.set_json(key, value, ttl)
            except Exception:  # pragma: no cover
                pass
        self._fallback.set_json(key, value, ttl)

    def cached_get_set(self, key: str, ttl: int, fetcher: Callable[[], Any]) -> Any:
        val = self.get_json(key)
        if val is not None:
            return val
        data = fetcher()
        self.set_json(key, data, ttl)
        return data

    def delete(self, key: str) -> None:
        if self._primary is not None:
            try:
                self._primary.delete(key)
            except Exception:
                pass
        self._fallback.delete(key)

    def delete_prefix(self, prefix: str) -> int:
        total = 0
        if self._primary is not None:
            try:
                total = self._primary.delete_prefix(prefix)
            except Exception:
                pass
        # Ensure local cache also cleared
        try:
            total_local = self._fallback.delete_prefix(prefix)
            # Prefer to return at least local deletions count if primary unavailable
            return total or total_local
        except Exception:
            return total


_cache_singleton: Optional[HybridCache] = None


def get_cache() -> HybridCache:
    global _cache_singleton
    if _cache_singleton is not None:
        return _cache_singleton

    # Build fallback first
    local = LocalTTLCache()

    primary: Optional[RedisJsonCache] = None
    url = getattr(settings, "REDIS_URL", None)
    prefix = getattr(settings, "REDIS_KEY_PREFIX", "seedtest:")
    if url:
        try:
            primary = RedisJsonCache(url=url, prefix=prefix)
            log.info("Using Redis cache at %s with prefix '%s'", url, prefix)
        except Exception as e:
            log.warning("Redis unavailable, falling back to local TTL cache: %s", e)
            primary = None

    _cache_singleton = HybridCache(primary=primary, fallback=local)
    return _cache_singleton
