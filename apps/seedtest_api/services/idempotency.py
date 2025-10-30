from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..models.idempotency import IdempotencyRecord
from ..settings import settings


_MEM_CACHE: dict[str, tuple[int, str, str, float]] = {}


def _mem_key(method: str, path: str, user_id: Optional[str], org_id: Optional[int], idem_key: str) -> str:
    return f"{method}:{path}:{user_id or ''}:{org_id or ''}:{idem_key}"


def compute_request_hash(body_obj: Any) -> str:
    try:
        if hasattr(body_obj, "model_dump"):
            payload = body_obj.model_dump()
        elif isinstance(body_obj, dict):
            payload = body_obj
        else:
            # Best-effort JSON encoding
            payload = json.loads(json.dumps(body_obj, default=str))
    except Exception:
        try:
            payload = json.loads(json.dumps(str(body_obj)))
        except Exception:
            payload = None
    j = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(j.encode("utf-8")).hexdigest()


@dataclass
class StoredResponse:
    status_code: int
    body_json: dict | list | str | int | float | bool | None
    headers_json: dict[str, Any] | None


def find_existing(
    session: Optional[Session],
    *,
    method: str,
    path: str,
    user_id: Optional[str],
    org_id: Optional[int],
    idem_key: str,
) -> Optional[tuple[str, StoredResponse]]:
    if not settings.ENABLE_IDEMPOTENCY:
        return None
    # Prefer DB when available
    if session is not None:
        rec = session.execute(
            select(IdempotencyRecord).where(
                IdempotencyRecord.method == method,
                IdempotencyRecord.path == path,
                IdempotencyRecord.user_id == user_id,
                IdempotencyRecord.org_id == org_id,
                IdempotencyRecord.idempotency_key == idem_key,
            )
        ).scalar_one_or_none()
        if rec is None:
            return None
        try:
            body_raw = rec.response_body  # type: ignore[assignment]
            body = json.loads(str(body_raw))
        except Exception:
            try:
                body = str(rec.response_body)
            except Exception:
                body = None
        headers = None
        try:
            headers_raw = rec.response_headers  # type: ignore[assignment]
            headers = json.loads(str(headers_raw)) if headers_raw is not None else None
        except Exception:
            headers = None
        try:
            status_code = int(rec.status_code)  # type: ignore[arg-type]
        except Exception:
            status_code = 200
        try:
            req_hash_val = str(rec.req_hash)
        except Exception:
            req_hash_val = ""
        return req_hash_val, StoredResponse(status_code=status_code, body_json=body, headers_json=headers)

    # In-memory fallback
    key = _mem_key(method, path, user_id, org_id, idem_key)
    ent = _MEM_CACHE.get(key)
    if not ent:
        return None
    status_code, body_s, headers_s, expiry = ent
    if expiry <= datetime.now(tz=timezone.utc).timestamp():
        _MEM_CACHE.pop(key, None)
        return None
    try:
        body = json.loads(body_s)
    except Exception:
        body = body_s
    try:
        headers = json.loads(headers_s) if headers_s else None
    except Exception:
        headers = None
    # We don't store req_hash in mem-cache; treat as identical
    return "", StoredResponse(status_code=status_code, body_json=body, headers_json=headers)


def store_result(
    session: Optional[Session],
    *,
    method: str,
    path: str,
    user_id: Optional[str],
    org_id: Optional[int],
    idem_key: str,
    req_hash: str,
    status_code: int,
    body: Any,
    headers: Optional[dict[str, Any]] = None,
) -> None:
    if not settings.ENABLE_IDEMPOTENCY:
        return
    ttl = int(settings.IDEMPOTENCY_TTL_SECS or 0) or 86400
    expires_at = datetime.now(tz=timezone.utc) + timedelta(seconds=ttl)
    body_s = json.dumps(body, default=str)
    headers_s = json.dumps(headers or {}, default=str)
    if session is not None:
        rec = IdempotencyRecord(
            method=method,
            path=path,
            user_id=user_id,
            org_id=org_id,
            idempotency_key=idem_key,
            req_hash=req_hash,
            status_code=int(status_code),
            response_body=body_s,
            response_headers=headers_s,
            expires_at=expires_at,
        )
        try:
            session.add(rec)
            session.flush()
        except IntegrityError:
            # Another request created it concurrently; ignore
            session.rollback()
        return

    # In-memory fallback
    key = _mem_key(method, path, user_id, org_id, idem_key)
    _MEM_CACHE[key] = (
        int(status_code),
        body_s,
        headers_s,
        expires_at.timestamp(),
    )
