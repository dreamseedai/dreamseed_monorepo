from __future__ import annotations

import hashlib
import json
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import text

from .db import get_session


def _hash_item_params(item_params: Any) -> str:
    try:
        blob = json.dumps(item_params, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(blob).hexdigest()
    except Exception:
        return ""


def ensure_model(name: str, version: str, hash_val: Optional[str] = None) -> int:
    """Return model_registry.id for (name, version), inserting if not exists."""
    with get_session() as s:
        # Try find existing
        row = s.execute(
            text("""
                SELECT id FROM model_registry
                WHERE name = :name AND version = :version
            """),
            {"name": name, "version": version},
        ).first()
        if row:
            return int(row[0])
        # Insert
        s.execute(
            text("""
                INSERT INTO model_registry(name, version, hash)
                VALUES (:name, :version, :hash)
            """),
            {"name": name, "version": version, "hash": hash_val},
        )
        row = s.execute(
            text("SELECT id FROM model_registry WHERE name=:name AND version=:version"),
            {"name": name, "version": version},
        ).first()
        return int(row[0])


def record_analysis_run(
    model_id: Optional[int], params: Dict[str, Any], status: str = "completed"
) -> int:
    with get_session() as s:
        s.execute(
            text(
                """
                INSERT INTO analysis_run(model_id, params, status, finished_at)
                VALUES (:model_id, CAST(:params AS JSON), :status, NOW())
                """
            ),
            {
                "model_id": model_id,
                "params": json.dumps(params, separators=(",", ":")),
                "status": status,
            },
        )
        row = s.execute(text("SELECT currval(pg_get_serial_sequence('analysis_run','id'))"))
        return int(row.scalar())


def log_analysis(run_id: int, level: str, message: str, meta: Optional[Dict[str, Any]] = None) -> None:
    with get_session() as s:
        s.execute(
            text(
                """
                INSERT INTO analysis_log(run_id, level, message, meta)
                VALUES (:run_id, :level, :message, CAST(:meta AS JSON))
                """
            ),
            {
                "run_id": run_id,
                "level": level,
                "message": message,
                "meta": json.dumps(meta or {}, separators=(",", ":")),
            },
        )


def persist_irt_calibration(
    model_name: str,
    item_params: Any,
    extra_meta: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Persist IRT calibration result: ensure model, record run with params.

    Stores item_params within analysis_run.params (compact JSON) and links to model.
    Returns { model_id, run_id }.
    """
    version = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    hash_val = _hash_item_params(item_params)
    try:
        model_id = ensure_model(model_name, version, hash_val)
    except Exception:
        model_id = None
    params = {
        "item_params": item_params,
        "meta": extra_meta or {},
        "version": version,
        "hash": hash_val,
    }
    run_id = None
    try:
        run_id = record_analysis_run(model_id, params, status="completed")
        log_analysis(run_id, "INFO", "IRT calibration persisted", {"items": len(item_params) if isinstance(item_params, list) else None})
    except Exception:
        pass
    return {"model_id": model_id, "run_id": run_id, "version": version, "hash": hash_val}
