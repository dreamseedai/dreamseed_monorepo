from __future__ import annotations

import os
from functools import lru_cache
from typing import Optional, Dict, List, Tuple
from datetime import datetime, timezone
import time

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Any

try:
    import redis  # type: ignore
except Exception:  # pragma: no cover
    redis = None  # type: ignore


class SelectionPolicy(BaseModel):
    prefer_balanced: bool = True
    deterministic: bool = False
    max_per_topic: Optional[int] = None
    # randomesque selection: choose randomly among top-K by info
    top_k_random: Optional[int] = None
    # alternative to top-K: pick within a fraction band of best score (kept for backward-compat)
    info_band_fraction: float = 0.05


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="ADAPTIVE_", case_sensitive=False)

    # Session backend: memory | redis
    session_backend: str = "memory"
    redis_url: str = "redis://localhost:6379/0"
    redis_key_prefix: str = "adaptive:"
    session_ttl_sec: int = 86400

    # Selection policy
    selection_prefer_balanced: bool = True
    selection_deterministic: bool = False
    selection_max_per_topic: Optional[int] = None
    selection_policy_ttl_sec: Optional[int] = None
    # Lightweight admin auth token (if set, all /api/settings endpoints require X-Admin-Token header)
    admin_token: Optional[str] = None
    # IRT re-estimation scheduler
    irt_update_enabled: bool = False
    irt_update_interval_sec: int = 3600
    # Database for IRT updater/reporting
    database_url: str | None = None
    irt_stats_view: str = "irt_item_stats"  # expected columns: question_id, a, b, c, correct_rate
    items_table: str = "items"  # table to persist updates (question_id, a, b, c)
    # IRT batch updater configuration
    irt_update_method: str = "heuristic"  # heuristic | mml | bayes (mml/bayes currently map to moment-based approx)
    irt_target_correct_rate: float = 0.5
    irt_learning_rate: float = 0.1
    irt_min_responses: int | None = None  # if stats view provides counts, require at least this many
    irt_update_max_items_per_run: int | None = None  # cap updates per cycle
    irt_change_log_table: str | None = None  # optional table to log param changes
    # Optional enrichment tables for solutions/topics and response aggregates
    questions_table: str | None = None  # expected columns: question_id, solution_html, topic
    responses_table: str | None = None  # expected columns: question_id, is_correct (bool)
    # Global exposure control
    item_exposure_table: str = "item_exposure"
    exposure_max_per_window: Optional[int] = None
    exposure_window_hours: int = 24

    # Ability estimator method: 'online' (default), 'mle', 'map', or 'eap'
    estimator_method: str = "online"
    # Default priors for MAP/EAP (used to initialize session state)
    estimator_prior_mean: float = 0.0
    estimator_prior_sd: float = 1.0

    # Scaled score transform parameters (scaled = mean_ref + sd_ref * theta)
    scale_mean_ref: float = 100.0
    scale_sd_ref: float = 15.0

    # Stopping rule configuration
    # Maximum number of questions before forced stop
    stop_max_items: int = 20
    # Optional time limit in seconds for an exam session; None disables time-based stopping
    stop_time_limit_sec: Optional[int] = 60
    # Standard error (SE) threshold for precision-based stopping
    stop_se_threshold: float = 0.3


_runtime_selection_overrides: Dict[str, SelectionPolicy] = {}
# Track runtime metadata (last_updated ISO8601, expire_at epoch seconds)
_runtime_selection_meta: Dict[str, Dict[str, object]] = {}
_SEL_POLICY_KEY = "selection_policy"


def _get_redis_client():
    s = get_settings()
    if redis is None:
        return None
    try:
        return redis.Redis.from_url(s.redis_url, decode_responses=True)  # type: ignore[attr-defined]
    except Exception:
        return None


@lru_cache(maxsize=1)
def get_settings() -> AppSettings:
    return AppSettings()  # type: ignore[call-arg]


def _ns_key(namespace: Optional[str]) -> str:
    return namespace or ""


def _fallback_chain(namespace: Optional[str]) -> List[Optional[str]]:
    """Generate a right-trim fallback chain for namespaces like 'a:b:c' -> ['a:b:c','a:b','a',None]."""
    if not namespace:
        return [None]
    parts = namespace.split(":")
    chain: List[Optional[str]] = []
    for i in range(len(parts), 0, -1):
        chain.append(":".join(parts[:i]))
    chain.append(None)
    return chain


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _check_runtime_expired(ns_key: str) -> None:
    meta = _runtime_selection_meta.get(ns_key)
    if not meta:
        return
    expire_at = meta.get("expire_at")
    if isinstance(expire_at, (int, float)) and time.time() >= float(expire_at):
        _runtime_selection_overrides.pop(ns_key, None)
        _runtime_selection_meta.pop(ns_key, None)


def get_selection_policy(namespace: Optional[str] = None, resolve_hierarchy: bool = False) -> SelectionPolicy:
    policy, _source, _resolved_ns, _last = get_selection_policy_info(namespace=namespace, resolve_hierarchy=resolve_hierarchy)
    return policy


def get_selection_policy_info(namespace: Optional[str] = None, resolve_hierarchy: bool = False) -> Tuple[SelectionPolicy, str, Optional[str], Optional[str]]:
    """Return (policy, source, resolved_namespace, last_updated ISO8601)."""
    key_ns = _ns_key(namespace)
    # Check runtime overrides first (with optional hierarchy)
    if resolve_hierarchy:
        for ns in _fallback_chain(namespace):
            ns_key = _ns_key(ns)
            _check_runtime_expired(ns_key)
            if ns_key in _runtime_selection_overrides:
                p = _runtime_selection_overrides[ns_key]
                last: Optional[str] = None
                meta = _runtime_selection_meta.get(ns_key)
                if meta and isinstance(meta.get("last_updated"), str):
                    lu = meta.get("last_updated")
                    last = lu if isinstance(lu, str) else None  
                return p, "runtime", (ns_key or None), last
    else:
        _check_runtime_expired(key_ns)
        if key_ns in _runtime_selection_overrides:
            p = _runtime_selection_overrides[key_ns]
            last: Optional[str] = None
            meta = _runtime_selection_meta.get(key_ns)
            if meta and isinstance(meta.get("last_updated"), str):
                lu = meta.get("last_updated")
                last = lu if isinstance(lu, str) else None  
            return p, "runtime", (key_ns or None), last
    # Try to load from Redis store if present
    r = _get_redis_client()
    if r is not None:
        try:
            prefixes: List[Tuple[str, Optional[str]]] = []
            if resolve_hierarchy:
                prefixes = [(f"{ns}:" if ns else "", ns) for ns in _fallback_chain(namespace)]
            else:
                prefixes = [(f"{namespace}:" if namespace else "", namespace)]
            for pfx, ns_val in prefixes:
                key = f"{get_settings().redis_key_prefix}{pfx}{_SEL_POLICY_KEY}"
                raw = r.get(key)
                if raw is not None:
                    import json

                    if isinstance(raw, (bytes, bytearray)):
                        raw = raw.decode("utf-8")
                    if isinstance(raw, str):
                        data = json.loads(raw)
                        # Legacy format: direct policy fields
                        if all(k in data for k in ("prefer_balanced", "deterministic")):
                            p = SelectionPolicy.model_validate(data)
                            return p, "redis", ns_val, None
                        # New format with metadata
                        if "policy" in data:
                            p = SelectionPolicy.model_validate(data["policy"])  # type: ignore[index]
                            last = data.get("last_updated")  # type: ignore[assignment]
                            return p, "redis", ns_val, last if isinstance(last, str) else None
        except Exception:
            pass
    s = get_settings()
    return (
        SelectionPolicy(
            prefer_balanced=s.selection_prefer_balanced,
            deterministic=s.selection_deterministic,
            max_per_topic=s.selection_max_per_topic,
            top_k_random=None,
            info_band_fraction=0.05,
        ),
        "env",
        None,
        None,
    )


def set_selection_policy(policy: SelectionPolicy, namespace: Optional[str] = None) -> None:
    key_ns = _ns_key(namespace)
    _runtime_selection_overrides[key_ns] = policy
    # Update runtime metadata and compute optional expiration
    s = get_settings()
    ttl = s.selection_policy_ttl_sec
    expire_at = time.time() + float(ttl) if ttl and ttl > 0 else None
    _runtime_selection_meta[key_ns] = {"last_updated": _now_iso(), "expire_at": expire_at}
    # Best-effort persist to Redis for multi-instance sharing
    r = _get_redis_client()
    if r is not None:
        try:
            import json
            payload = json.dumps({"policy": policy.model_dump(), "last_updated": _now_iso()})
            ttl = s.selection_policy_ttl_sec
            if ttl and ttl > 0:
                ns_part = f"{namespace}:" if namespace else ""
                r.setex(f"{s.redis_key_prefix}{ns_part}{_SEL_POLICY_KEY}", int(ttl), payload)
            else:
                ns_part = f"{namespace}:" if namespace else ""
                r.set(f"{s.redis_key_prefix}{ns_part}{_SEL_POLICY_KEY}", payload)
        except Exception:
            pass


def clear_selection_policy(namespace: Optional[str] = None) -> None:
    """Reset runtime overrides and remove Redis-stored policy so env defaults apply."""
    key_ns = _ns_key(namespace)
    if key_ns in _runtime_selection_overrides:
        del _runtime_selection_overrides[key_ns]
    if key_ns in _runtime_selection_meta:
        del _runtime_selection_meta[key_ns]
    r = _get_redis_client()
    if r is not None:
        try:
            s = get_settings()
            ns_part = f"{namespace}:" if namespace else ""
            r.delete(f"{s.redis_key_prefix}{ns_part}{_SEL_POLICY_KEY}")
        except Exception:
            pass


def list_selection_namespaces(include_global: bool = True) -> List[str]:
    """Enumerate namespaces that have a stored policy (in Redis or runtime memory cache)."""
    found: set[str] = set()
    # Always include global namespace for visibility when requested
    if include_global:
        found.add("")
    # From memory overrides
    for ns in _runtime_selection_overrides.keys():
        if ns:
            found.add(ns)
        elif include_global:
            found.add("")
    # From Redis
    r = _get_redis_client()
    if r is not None:
        try:
            prefix = get_settings().redis_key_prefix
            pattern = f"{prefix}*{_SEL_POLICY_KEY}"
            for key in r.scan_iter(match=pattern):  # type: ignore[attr-defined]
                # key like: {prefix}{ns:}selection_policy or {prefix}selection_policy
                skey = key
                if isinstance(skey, (bytes, bytearray)):
                    skey = skey.decode("utf-8")
                if isinstance(skey, str) and skey.startswith(prefix):
                    suffix = skey[len(prefix):]
                    if suffix == _SEL_POLICY_KEY:
                        if include_global:
                            found.add("")
                    else:
                        # remove trailing 'selection_policy' and potential trailing ':' before it
                        ns_part = suffix[: -(len(_SEL_POLICY_KEY))]
                        if ns_part.endswith(":"):
                            ns_part = ns_part[:-1]
                        if ns_part:
                            found.add(ns_part)
        except Exception:
            pass
    # Return sorted for stability, with global first if included
    out = sorted([ns for ns in found if ns])
    if include_global and "" in found:
        return [""] + out
    return out
