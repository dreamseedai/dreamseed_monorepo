from __future__ import annotations

import json
import math
import os
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from statistics import median
from typing import Any, Dict, Iterable, List, Optional, Tuple

import sqlalchemy as sa
from sqlalchemy.orm import Session


# --------- Data model (lightweight) ---------
@dataclass
class Attempt:
    question_id: Optional[str]
    topic_id: Optional[str]
    is_correct: Optional[bool]
    responded_at: Optional[datetime]
    response_time_ms: Optional[int]
    used_hints: Optional[int]
    session_id: Optional[str]
    session_duration_s: Optional[int]


# --------- Time helpers ---------


def week_start(d: date) -> date:
    """Return ISO week Monday for given date."""
    # Monday is 0 in Python weekday()
    dow = d.weekday()
    monday = d - timedelta(days=dow)
    return monday


def time_window(as_of: date, days: int) -> Tuple[datetime, datetime]:
    """Return (start,end) UTC datetimes inclusive for days ending at as_of."""
    end_dt = datetime(
        as_of.year, as_of.month, as_of.day, 23, 59, 59, tzinfo=timezone.utc
    )
    start_dt = end_dt - timedelta(days=days - 1)
    return start_dt, end_dt


# --------- Fetchers ---------


def _fetch_exam_results_rows(
    session: Session, user_id: str, start: datetime, end: datetime
) -> list:
    sql = sa.text(
        """
        SELECT session_id,
               COALESCE(updated_at, created_at) AS ts,
               result_json
        FROM exam_results
        WHERE user_id = :uid
          AND COALESCE(updated_at, created_at) BETWEEN :st AND :en
        ORDER BY COALESCE(updated_at, created_at)
        LIMIT 500
        """
    )
    rows = (
        session.execute(sql, {"uid": user_id, "st": start, "en": end}).mappings().all()
    )
    return list(rows)


def load_attempts(
    session: Session, user_id: str, start: datetime, end: datetime
) -> List[Attempt]:
    rows = _fetch_exam_results_rows(session, user_id, start, end)
    attempts: List[Attempt] = []
    for r in rows:
        ts = r.get("ts")
        doc = r.get("result_json") or {}
        qs = doc.get("questions") or []
        # Derive a best-effort dwell time per session
        dwell = 0
        for q in qs:
            tsec = q.get("time_spent_sec")
            if isinstance(tsec, (int, float)):
                dwell += int(tsec)
        dwell = dwell or None
        for q in qs:
            attempts.append(
                Attempt(
                    question_id=(
                        str(q.get("question_id"))
                        if q.get("question_id") is not None
                        else None
                    ),
                    topic_id=(
                        str(q.get("topic")) if q.get("topic") is not None else None
                    ),
                    is_correct=(
                        bool(q.get("is_correct") or q.get("correct"))
                        if (
                            q.get("is_correct") is not None
                            or q.get("correct") is not None
                        )
                        else None
                    ),
                    responded_at=ts,
                    response_time_ms=(
                        int(float(q.get("time_spent_sec")) * 1000)
                        if isinstance(q.get("time_spent_sec"), (int, float))
                        else None
                    ),
                    used_hints=(
                        int(q.get("used_hints"))
                        if isinstance(q.get("used_hints"), (int, float))
                        else None
                    ),
                    session_id=r.get("session_id"),
                    session_duration_s=dwell,
                )
            )
    return attempts


# --------- Compute functions (MVP) ---------


def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def compute_improvement_index(
    session: Session,
    user_id: str,
    as_of: date,
    window_days: int = 14,
) -> Optional[float]:
    """Compute improvement index I_t.

    Prefer theta-based delta over two half-windows within the last 28 days, with exposure and SE-based penalty.
    Fallback: accuracy delta if theta unavailable.

    When METRICS_USE_IRT_THETA=true and sufficient exposure:
    - Uses theta delta: I_t = clamp((θ_recent - θ_prev) * exposure_adj * penalty_from_se, -1, 1)
    - Windows: prev=[as_of-27..as_of-14], recent=[as_of-13..as_of] (14-day windows)
    - exposure_adj = min(1.0, n_recent/30)
    - penalty_from_se = 1 - min(0.5, 1.96 * se_recent)
    """
    # Define windows per spec: prev=[as_of-27..as_of-14], recent=[as_of-13..as_of]
    # Total window is 28 days split into two 14-day windows
    prev_start = as_of - timedelta(days=27)
    prev_end = as_of - timedelta(days=14)
    recent_start = as_of - timedelta(days=13)
    recent_end = as_of

    # Exposure from recent responses count
    recent_attempts = load_attempts(session, user_id, *time_window(recent_end, 14))
    n_recent = sum(1 for a in recent_attempts if a.is_correct is not None)
    exposure_adj = min(1.0, n_recent / 30.0)

    # Try theta mode only if enabled and we have some recent exposure to anchor the estimate
    use_theta = os.getenv("METRICS_USE_IRT_THETA", "false").lower() == "true"
    if use_theta and n_recent >= 5:
        theta_prev = _latest_theta_in_window(session, user_id, prev_start, prev_end)
        theta_recent = _latest_theta_in_window(
            session, user_id, recent_start, recent_end
        )
        if theta_prev is not None and theta_recent is not None:
            t_prev, _ = theta_prev
            t_recent, se_recent = theta_recent
            se_penalty = 1.0
            if se_recent is not None:
                se_penalty = 1.0 - min(0.5, 1.96 * float(se_recent))
            delta = float(t_recent) - float(t_prev)
            return _clamp(delta * exposure_adj * se_penalty, -1.0, 1.0)

    # Fallback: accuracy-based delta on two windows of 14 days each
    # recent window
    r_start_dt, r_end_dt = time_window(as_of, 14)
    recent = load_attempts(session, user_id, r_start_dt, r_end_dt)
    n_recent_acc = sum(1 for a in recent if a.is_correct is not None)
    c_recent = sum(1 for a in recent if a.is_correct is True)
    # previous window
    prev_as_of = as_of - timedelta(days=14)
    p_start_dt, p_end_dt = time_window(prev_as_of, 14)
    prev = load_attempts(session, user_id, p_start_dt, p_end_dt)
    n_prev = sum(1 for a in prev if a.is_correct is not None)
    c_prev = sum(1 for a in prev if a.is_correct is True)

    if n_recent_acc == 0 or n_prev == 0:
        return None

    p_recent = c_recent / n_recent_acc
    p_prev = c_prev / n_prev
    delta = p_recent - p_prev

    ci_width = 1.96 * math.sqrt(p_recent * (1.0 - p_recent) / max(1, n_recent_acc))
    penalty = 1.0 - min(0.5, ci_width)

    return _clamp(delta * exposure_adj * penalty, -1.0, 1.0)


def compute_time_efficiency(
    session: Session,
    user_id: str,
    as_of: date,
    window_days: int = 28,
) -> Optional[float]:
    r_start, r_end = time_window(as_of, window_days)
    recent = [
        a.response_time_ms
        for a in load_attempts(session, user_id, r_start, r_end)
        if (a.is_correct is True and isinstance(a.response_time_ms, int))
    ]

    prev_as_of = as_of - timedelta(days=window_days)
    p_start, p_end = time_window(prev_as_of, window_days)
    prev = [
        a.response_time_ms
        for a in load_attempts(session, user_id, p_start, p_end)
        if (a.is_correct is True and isinstance(a.response_time_ms, int))
    ]

    if len(prev) == 0 or len(recent) == 0:
        return None

    med_prev = float(median(prev))
    med_recent = float(median(recent))
    if med_prev <= 0:
        return None
    return _clamp((med_prev - med_recent) / med_prev, 0.0, 1.0)


def compute_recovery_rate(
    session: Session,
    user_id: str,
    as_of: date,
    window_days: int = 28,
) -> Optional[float]:
    r_start, r_end = time_window(as_of, window_days)
    prev_as_of = as_of - timedelta(days=window_days)
    p_start, p_end = time_window(prev_as_of, window_days)

    recent = load_attempts(session, user_id, r_start, r_end)
    prev = load_attempts(session, user_id, p_start, p_end)

    # Map by question_id; fallback to topic-level if question_id missing
    prev_incorrect: Dict[Tuple[str, Optional[str]], int] = {}
    for a in prev:
        key = (str(a.question_id) if a.question_id else "", a.topic_id)
        if a.is_correct is False:
            prev_incorrect[key] = prev_incorrect.get(key, 0) + 1

    if not prev_incorrect:
        return None

    recovered = 0
    total = 0
    for a in recent:
        key = (str(a.question_id) if a.question_id else "", a.topic_id)
        if key in prev_incorrect:
            total += 1
            if a.is_correct is True:
                recovered += 1

    if total == 0:
        return None
    return max(0.0, min(1.0, recovered / total))


def compute_engagement(
    session: Session,
    user_id: str,
    as_of: date,
    window_days: int = 28,
) -> Optional[float]:
    start, end = time_window(as_of, window_days)
    attempts = load_attempts(session, user_id, start, end)
    if not attempts:
        return None

    # Sessions
    sessions: Dict[str, List[Attempt]] = {}
    for a in attempts:
        sid = a.session_id or ""
        sessions.setdefault(sid, []).append(a)

    # session_count_norm: assume 1 per day is ideal -> 28 => 1.0
    session_count_norm = max(0.0, min(1.0, len(sessions) / float(window_days)))

    # gap consistency: use session timestamps (responded_at)
    ts = sorted(
        {a.responded_at for a in attempts if isinstance(a.responded_at, datetime)}
    )
    if len(ts) >= 2:
        gaps = []
        for i in range(1, len(ts)):
            gaps.append((ts[i] - ts[i - 1]).total_seconds() / 86400.0)
        mean_gap = sum(gaps) / len(gaps)
        inv_gap = 1.0 / mean_gap if mean_gap > 0 else 1.0
        gap_norm = max(0.0, min(1.0, inv_gap))  # >=1/day caps at 1
    else:
        gap_norm = 0.5

    # hints_norm: prefer fewer hints -> invert average hints per attempt
    hints_vals = [a.used_hints for a in attempts if isinstance(a.used_hints, int)]
    if hints_vals:
        avg_hints = sum(hints_vals) / len(hints_vals)
        hints_norm = max(0.0, min(1.0, 1.0 - (avg_hints / 3.0)))  # 3+ hints => 0
    else:
        hints_norm = 0.5

    # dwell_norm: average session duration (s), 15+ minutes maps to 1.0
    sess_durations = [
        a.session_duration_s for a in attempts if isinstance(a.session_duration_s, int)
    ]
    if sess_durations:
        avg_dwell = sum(sess_durations) / max(1, len(sessions))
        dwell_norm = max(0.0, min(1.0, avg_dwell / 900.0))
    else:
        dwell_norm = 0.5

    engagement = (
        0.35 * session_count_norm
        + 0.25 * gap_norm
        + 0.2 * hints_norm
        + 0.2 * dwell_norm
    )
    return max(0.0, min(1.0, engagement))


# --------- Upsert and orchestrator ---------


def upsert_weekly_kpi(
    session: Session,
    user_id: str,
    week_start: date,
    kpis: Dict[str, Any],
) -> None:
    payload = json.dumps(kpis)
    stmt = sa.text(
        """
        INSERT INTO weekly_kpi (user_id, week_start, kpis, created_at, updated_at)
        VALUES (:uid, :ws, CAST(:k::text AS jsonb), NOW(), NOW())
        ON CONFLICT (user_id, week_start)
        DO UPDATE SET kpis = EXCLUDED.kpis, updated_at = NOW()
        """
    )
    session.execute(stmt, {"uid": user_id, "ws": week_start, "k": payload})
    session.commit()


def calculate_and_store_weekly_kpi(
    session: Session,
    user_id: str,
    week_start_val: date,
    target: Optional[float] = None,
) -> Dict[str, Any]:
    # Use end-of-week as_of for windows
    week_end = week_start_val + timedelta(days=6)
    I_t = compute_improvement_index(session, user_id, week_end, window_days=14)
    E_t = compute_time_efficiency(session, user_id, week_end, window_days=28)
    R_t = compute_recovery_rate(session, user_id, week_end, window_days=28)
    A_t = compute_engagement(session, user_id, week_end, window_days=28)
    # Compute P(goal|state) using ability summary; S left for next contract
    P = compute_goal_attainment_probability(session, user_id, target)
    # Compute churn risk S(t) using heuristic over recent activity
    as_of = week_start_val + timedelta(days=6)
    S = compute_churn_risk(session, user_id, as_of)
    kpis = {"I_t": I_t, "E_t": E_t, "R_t": R_t, "A_t": A_t, "P": P, "S": S}
    upsert_weekly_kpi(session, user_id, week_start_val, kpis)
    return {"user_id": user_id, "week_start": week_start_val, "kpis": kpis}


def list_weekly_kpi(session: Session, user_id: str, weeks: int) -> list[dict]:
    """Return recent weekly KPI rows for a user, newest first, limited by weeks.

    Each item: {user_id: str, week_start: date, kpis: dict}
    """
    stmt = sa.text(
        """
        SELECT user_id, week_start, kpis
        FROM weekly_kpi
        WHERE user_id = :uid
        ORDER BY week_start DESC
        LIMIT :lim
        """
    )
    rows = (
        session.execute(stmt, {"uid": user_id, "lim": int(max(0, weeks))})
        .mappings()
        .all()
    )
    out: list[dict] = []
    for r in rows:
        ws = r.get("week_start")
        # Ensure week_start is a date (DB may return datetime/date)
        if isinstance(ws, datetime):
            ws_date = ws.date()
        else:
            ws_date = ws
        out.append(
            {
                "user_id": r.get("user_id"),
                "week_start": ws_date,
                "kpis": r.get("kpis")
                or {
                    "I_t": None,
                    "E_t": None,
                    "R_t": None,
                    "A_t": None,
                    "P": None,
                    "S": None,
                },
            }
        )
    return out


def _latest_theta_in_window(
    session: Session, user_id: str, start_d: date, end_d: date
) -> Optional[Tuple[float, Optional[float]]]:
    """Fetch the latest theta (and se) for user within [start_d, end_d].

    Prefers `mirt_ability` fitted_at; falls back to averaging `student_topic_theta` updated_at with inverse-variance weighting.
    """
    # First: mirt_ability
    try:
        stmt = sa.text(
            """
            SELECT theta, se
            FROM mirt_ability
            WHERE user_id = :uid
              AND fitted_at BETWEEN :st AND :en
            ORDER BY fitted_at DESC
            LIMIT 1
            """
        )
        st_dt = datetime(
            start_d.year, start_d.month, start_d.day, 0, 0, 0, tzinfo=timezone.utc
        )
        en_dt = datetime(
            end_d.year, end_d.month, end_d.day, 23, 59, 59, tzinfo=timezone.utc
        )
        row = session.execute(stmt, {"uid": user_id, "st": st_dt, "en": en_dt}).first()
        if row is not None:
            th = row[0]
            se = row[1]
            if th is not None:
                return float(th), (float(se) if se is not None else None)
    except Exception:
        pass
    # Fallback: student_topic_theta aggregate
    try:
        stmt2 = sa.text(
            """
            SELECT theta, se, fitted_at
            FROM student_topic_theta
            WHERE user_id = :uid AND fitted_at BETWEEN :st AND :en
            ORDER BY fitted_at DESC
            LIMIT 200
            """
        )
        st_dt = datetime(
            start_d.year, start_d.month, start_d.day, 0, 0, 0, tzinfo=timezone.utc
        )
        en_dt = datetime(
            end_d.year, end_d.month, end_d.day, 23, 59, 59, tzinfo=timezone.utc
        )
        rows = session.execute(
            stmt2, {"uid": user_id, "st": st_dt, "en": en_dt}
        ).fetchall()
        if not rows:
            return None
        # inverse-variance weighting if SE provided
        num = 0.0
        den = 0.0
        for th, se, _ in rows:
            try:
                th_f = float(th)
            except Exception:
                continue
            if se is None or float(se) <= 0:
                w = 1.0
            else:
                w = 1.0 / float(se) ** 2
            num += w * th_f
            den += w
        if den <= 0:
            return None
        theta_mean = num / den
        # approximate se from weights
        se_approx = (1.0 / math.sqrt(den)) if den > 0 else None
        return float(theta_mean), (float(se_approx) if se_approx is not None else None)
    except Exception:
        return None


# --------- Goal attainment probability (P) ---------


def _get_default_target() -> float:
    try:
        return float(os.getenv("METRICS_DEFAULT_TARGET", "0.0"))
    except Exception:
        return 0.0


def load_user_ability_summary(
    session: Session, user_id: str
) -> Optional[Tuple[float, float]]:
    """Load (mu, sd) ability summary for user if available.

    Tries ability_estimates table with columns (user_id, mean, sd, fitted_at?)
    Returns tuple (mean, sd) or None if unavailable.
    """
    try:
        stmt = sa.text(
            """
            SELECT mean, sd
            FROM ability_estimates
            WHERE user_id = :uid
            ORDER BY COALESCE(fitted_at, updated_at, created_at) DESC
            LIMIT 1
            """
        )
        row = session.execute(stmt, {"uid": user_id}).first()
        if not row:
            return None
        mean_val = row[0]
        sd_val = row[1]
        if mean_val is None or sd_val is None:
            return None
        try:
            return (float(mean_val), float(sd_val))
        except Exception:
            return None
    except Exception:
        # Table might not exist or query failed; treat as unavailable
        return None


def _normal_cdf(z: float) -> float:
    import math

    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def _normal_goal_prob(mu: float, sd: float, target: float) -> Optional[float]:
    if sd is None or sd <= 0:
        return None
    try:
        z = (target - mu) / sd
        p = 1.0 - _normal_cdf(z)
        return max(0.0, min(1.0, float(p)))
    except Exception:
        return None


def compute_goal_attainment_probability(
    session: Session, user_id: str, target: Optional[float] = None
) -> Optional[float]:
    """Compute P(goal|state) using Normal approximation by default.

    If METRICS_USE_BAYESIAN=true, attempts a Bayesian client, and falls back on Normal
    when client is unavailable or raises.
    """
    # Resolve target
    if target is None:
        target = _get_default_target()

    # Optional Bayesian path (placeholder for future integration)
    use_bayes = os.getenv("METRICS_USE_BAYESIAN", "false").lower() == "true"
    if use_bayes:
        try:  # pragma: no cover - placeholder; will be covered when client lands
            from ..app.clients import r_brms as rbrms  # type: ignore

            mu_sd = load_user_ability_summary(session, user_id)
            if not mu_sd:
                return None
            mu, sd = mu_sd
            # Suppose r_brms client expects mu, sd, target -> probability in [0,1]
            prob = rbrms.prob_goal(mu=mu, sd=sd, target=target)  # type: ignore[attr-defined]
            return max(0.0, min(1.0, float(prob)))
        except Exception:
            # Fallback to Normal approx
            pass

    mu_sd = load_user_ability_summary(session, user_id)
    if not mu_sd:
        return None
    mu, sd = mu_sd
    return _normal_goal_prob(mu, sd, float(target))


# --------- Topic theta loader (IRT integration) ---------


def load_topic_thetas(
    session: Session, user_id: str, as_of: date, window_days: int = 28
) -> List[Dict[str, Any]]:
    """Load topic-level theta estimates for a user within a window ending at as_of.

    Returns list of dicts with keys: topic_id, theta, se, model, fitted_at.
    Prefers student_topic_theta; falls back to general mirt_ability if topic-level unavailable.
    """
    start_dt = datetime(
        (as_of - timedelta(days=window_days)).year,
        (as_of - timedelta(days=window_days)).month,
        (as_of - timedelta(days=window_days)).day,
        0,
        0,
        0,
        tzinfo=timezone.utc,
    )
    end_dt = datetime(
        as_of.year, as_of.month, as_of.day, 23, 59, 59, tzinfo=timezone.utc
    )

    # Try topic-level first
    try:
        stmt = sa.text(
            """
            SELECT topic_id, theta, se, model, fitted_at
            FROM student_topic_theta
            WHERE user_id = :uid AND fitted_at BETWEEN :st AND :en
            ORDER BY fitted_at DESC
            LIMIT 200
            """
        )
        rows = (
            session.execute(stmt, {"uid": user_id, "st": start_dt, "en": end_dt})
            .mappings()
            .all()
        )
        if rows:
            out: List[Dict[str, Any]] = []
            for r in rows:
                out.append(
                    {
                        "topic_id": r.get("topic_id"),
                        "theta": (
                            float(r.get("theta"))
                            if r.get("theta") is not None
                            else None
                        ),
                        "se": float(r.get("se")) if r.get("se") is not None else None,
                        "model": str(r.get("model") or "mirt"),
                        "fitted_at": r.get("fitted_at"),
                    }
                )
            return out
    except Exception:
        pass

    # Fallback: general ability from mirt_ability
    try:
        stmt2 = sa.text(
            """
            SELECT theta, se, model, fitted_at
            FROM mirt_ability
            WHERE user_id = :uid AND fitted_at BETWEEN :st AND :en
            ORDER BY fitted_at DESC
            LIMIT 1
            """
        )
        row = (
            session.execute(stmt2, {"uid": user_id, "st": start_dt, "en": end_dt})
            .mappings()
            .first()
        )
        if row:
            return [
                {
                    "topic_id": None,  # General ability, not topic-specific
                    "theta": (
                        float(row.get("theta"))
                        if row.get("theta") is not None
                        else None
                    ),
                    "se": float(row.get("se")) if row.get("se") is not None else None,
                    "model": str(row.get("model") or "mirt"),
                    "fitted_at": row.get("fitted_at"),
                }
            ]
    except Exception:
        pass

    return []


# --------- Churn risk S(t) (heuristic MVP) ---------


def _get_churn_horizon_days() -> int:
    try:
        return int(os.getenv("METRICS_CHURN_HORIZON_DAYS", "14"))
    except Exception:
        return 14


def load_user_session_stats(
    session: Session, user_id: str, lookback_days: int = 56
) -> Optional[Dict[str, Any]]:
    """Load session/activity summary from available sources.

    Fallback uses exam_results timestamps as session surrogates.
    Returns dict with keys: last_seen (date), sessions (int), mean_gap_days (float), first_seen (date).
    Returns None if no activity found.
    """
    # Compute window bounds
    today = date.today()
    start_dt = datetime(
        today.year, today.month, today.day, 0, 0, 0, tzinfo=timezone.utc
    ) - timedelta(days=lookback_days - 1)
    end_dt = datetime(
        today.year, today.month, today.day, 23, 59, 59, tzinfo=timezone.utc
    )

    try:
        # Try to derive from exam_results if dedicated tables not available
        sql = sa.text(
            """
            SELECT session_id, COALESCE(updated_at, created_at) AS ts
            FROM exam_results
            WHERE user_id = :uid
              AND COALESCE(updated_at, created_at) BETWEEN :st AND :en
            ORDER BY COALESCE(updated_at, created_at)
            LIMIT 1000
            """
        )
        rows = (
            session.execute(sql, {"uid": user_id, "st": start_dt, "en": end_dt})
            .mappings()
            .all()
        )
        if not rows:
            return None
        # Build sorted unique timestamps per session (basic surrogate)
        ts_list = [r.get("ts") for r in rows if r.get("ts") is not None]
        # Ensure only datetimes
        ts_list = [t for t in ts_list if isinstance(t, datetime)]
        if not ts_list:
            return None
        ts_list = sorted(ts_list)
        last_seen_dt: datetime = ts_list[-1]
        first_seen_dt: datetime = ts_list[0]
        # Sessions: count distinct session_id
        sess_ids = set(
            str(r.get("session_id")) for r in rows if r.get("session_id") is not None
        )
        sessions_cnt = len(sess_ids)
        # Mean gap in days between consecutive timestamps
        gaps: List[float] = []
        for i in range(1, len(ts_list)):
            gaps.append((ts_list[i] - ts_list[i - 1]).total_seconds() / 86400.0)
        mean_gap = sum(gaps) / len(gaps) if gaps else 0.0
        return {
            "last_seen": last_seen_dt.date(),
            "first_seen": first_seen_dt.date(),
            "sessions": sessions_cnt,
            "mean_gap_days": float(mean_gap),
        }
    except Exception:
        # On any failure, treat as unavailable
        return None


def compute_churn_risk(
    session: Session, user_id: str, as_of: date, horizon_days: Optional[int] = None
) -> Optional[float]:
    """Compute heuristic churn risk S(t) over a given horizon.

    Returns None if no activity available to assess risk.
    """
    if horizon_days is None:
        horizon_days = _get_churn_horizon_days()
    stats = load_user_session_stats(session, user_id)
    if not stats or not stats.get("last_seen"):
        return None
    try:
        last_seen: date = stats["last_seen"]  # type: ignore[assignment]
        d = max(0, (as_of - last_seen).days)
        base = _clamp(d / float(max(1, int(horizon_days))), 0.0, 1.0)
        sessions = max(0, int(stats.get("sessions") or 0))
        mean_gap = float(stats.get("mean_gap_days") or 0.0)
        sc_norm = _clamp(1.0 - (sessions / 10.0), 0.0, 1.0)
        gap_norm = _clamp(mean_gap / 7.0, 0.0, 1.0)
        risk = _clamp(0.6 * base + 0.25 * gap_norm + 0.15 * sc_norm, 0.0, 1.0)
        return risk
    except Exception:
        return None
