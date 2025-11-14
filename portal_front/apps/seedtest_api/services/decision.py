"""
Decision helpers for gap detection, scheduling, and adaptive difficulty.
"""
from __future__ import annotations
from datetime import date, timedelta
from typing import Any, Dict, List, Optional, Tuple
import os

from sqlalchemy import text
from sqlalchemy.engine import Connection


def _env_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except Exception:
        return default


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except Exception:
        return default


def _latest_theta(conn: Connection, user_id: str) -> Optional[Tuple[float, Optional[float]]]:
    row = conn.execute(
        text("SELECT theta, se FROM mirt_ability WHERE user_id=:u ORDER BY fitted_at DESC LIMIT 1"),
        {"u": user_id},
    ).fetchone()
    if not row:
        return None
    return float(row[0]), (float(row[1]) if row[1] is not None else None)


def detect_mastery_gaps(
    conn: Connection,
    user_id: str,
    lookback_days: int = 28,
    theta_threshold: Optional[float] = None,
    sd_threshold: Optional[float] = None,
    top_n: int = 5,
) -> List[Dict[str, Any]]:
    """Detect topics with low theta_mean and high theta_sd in the recent window.
    Returns [{topic_id, theta_mean, theta_sd, priority_score}] sorted by priority.
    """
    theta_thr = theta_threshold if theta_threshold is not None else _env_float("GAP_THETA_THRESHOLD", 0.0)
    sd_thr = sd_threshold if sd_threshold is not None else _env_float("GAP_SD_THRESHOLD", 0.5)
    since = (date.today() - timedelta(days=lookback_days))
    rows = conn.execute(
        text(
            """
            SELECT topic_id::text, AVG(theta_mean)::float8 AS tm, AVG(theta_sd)::float8 AS ts
            FROM features_topic_daily
            WHERE student_id=:u AND date >= :since AND theta_mean IS NOT NULL
            GROUP BY topic_id
            """
        ),
        {"u": user_id, "since": since},
    ).fetchall()
    out: List[Dict[str, Any]] = []
    for r in rows:
        tm = float(r[1]) if r[1] is not None else None
        ts = float(r[2]) if r[2] is not None else None
        if tm is None or ts is None:
            continue
        if tm < theta_thr and ts >= sd_thr:
            # priority: lower theta and higher sd => higher priority
            score = (theta_thr - tm) * (1.0 + ts)
            out.append({"topic_id": r[0], "theta_mean": tm, "theta_sd": ts, "priority_score": score})
    out.sort(key=lambda x: x["priority_score"], reverse=True)
    return out[:top_n]


def recommend_schedule(
    conn: Connection,
    user_id: str,
    top_n: int = 5,
    weights: Optional[Dict[str, float]] = None,
) -> List[Dict[str, Any]]:
    """Select Top-N topics by weighted score (gap/time-efficiency proxy), and propose spaced schedule dates.
    Returns [{topic_id, score, sessions: [{date, minutes}...]}]
    """
    w = {"gap": 0.6, "time": 0.4}
    if weights:
        w.update(weights)
    # gap proxy: (1 - mean acc)
    # time-efficiency proxy: lower rt_median is better => normalize
    since = (date.today() - timedelta(days=28))
    rows = conn.execute(
        text(
            """
            SELECT topic_id::text,
                   AVG(acc)::float8 AS acc,
                   PERCENTILE_DISC(0.5) WITHIN GROUP (ORDER BY rt_median) AS rt_med
            FROM features_topic_daily
            WHERE student_id=:u AND date >= :since
            GROUP BY topic_id
            """
        ),
        {"u": user_id, "since": since},
    ).fetchall()
    if not rows:
        return []
    # Compute normalized time-efficiency: invert and min-max
    vals = [float(r[2]) for r in rows if r[2] is not None]
    rt_min = min(vals) if vals else 0.0
    rt_max = max(vals) if vals else 1.0
    out: List[Dict[str, Any]] = []
    for r in rows:
        topic = r[0]
        acc = float(r[1]) if r[1] is not None else 0.0
        rt = float(r[2]) if r[2] is not None else rt_max
        gap_score = max(0.0, min(1.0, 1.0 - acc))
        time_eff = 0.0 if rt_max == rt_min else max(0.0, min(1.0, (rt_max - rt) / (rt_max - rt_min)))
        score = w["gap"] * gap_score + w["time"] * time_eff
        out.append({"topic_id": topic, "score": score})
    out.sort(key=lambda x: x["score"], reverse=True)
    sel = out[:top_n]
    # simple spacing: +1, +3, +7 days; 25min each
    base = date.today()
    for s in sel:
        s["sessions"] = [
            {"date": (base + timedelta(days=1)).isoformat(), "minutes": 25},
            {"date": (base + timedelta(days=3)).isoformat(), "minutes": 25},
            {"date": (base + timedelta(days=7)).isoformat(), "minutes": 25},
        ]
    return sel


def adaptive_items(
    conn: Connection,
    user_id: str,
    topic_id: str,
    target_p: float = 0.7,
    bandwidth: float = 0.1,
    limit: int = 10,
) -> List[Dict[str, Any]]:
    """Select items in topic such that expected P(correct) ≈ target_p using IRT params and latest theta.
    Returns [{item_id, p}] sorted by closeness to target.
    """
    th = _latest_theta(conn, user_id)
    if not th:
        return []
    theta, _ = th
    # Load item params for topic
    rows = conn.execute(
        text(
            """
            SELECT q.id::bigint AS item_id,
                   (q.meta->'irt'->>'a')::float AS a,
                   (q.meta->'irt'->>'b')::float AS b,
                   (q.meta->'irt'->>'c')::float AS c
            FROM question q
            WHERE q.topic_id::text = :tid AND q.meta->'irt' IS NOT NULL
            """
        ),
        {"tid": topic_id},
    ).fetchall()
    sel: List[Dict[str, Any]] = []
    for r in rows:
        a = float(r[1]) if r[1] is not None else 1.0
        b = float(r[2]) if r[2] is not None else 0.0
        c = float(r[3]) if r[3] is not None else 0.0
        import math
        logistic = 1.0 / (1.0 + math.exp(-a * (theta - b)))
        p = c + (1.0 - c) * logistic
        if abs(p - target_p) <= bandwidth:
            sel.append({"item_id": int(r[0]), "p": float(p)})
    sel.sort(key=lambda x: abs(x["p"] - target_p))
    return sel[:limit]


def enqueue_churn_alert(conn: Connection, user_id: str, s_risk: float) -> None:
    th = _env_float("CHURN_ALERT_THRESHOLD", 0.7)
    if s_risk < th:
        return
    # ensure table
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS alert_queue (
              id BIGSERIAL PRIMARY KEY,
              user_id TEXT NOT NULL,
              alert_type TEXT NOT NULL,
              payload JSONB,
              status TEXT NOT NULL DEFAULT 'pending',
              created_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
            """
        )
    )
    import json
    conn.execute(
        text(
            """
            INSERT INTO alert_queue (user_id, alert_type, payload)
            VALUES (:u, :t, to_jsonb(:p::json))
            """
        ),
        {"u": user_id, "t": "churn_high", "p": json.dumps({"risk": s_risk})},
    )
