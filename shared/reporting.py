"""Reporting utilities for adaptive exams.

Computes final ability (theta), standard error (SE), confidence interval,
optional scaled score and percentile, topic-wise summary, and lightweight
recommendations. Designed to be called from API endpoints or batch jobs.

Contract
--------
Inputs (dict):
- items: list of dicts, each with at minimum: {id, a, b, c(optional), topic(optional), correct(bool|int), time_spent_sec(optional), solution(optional)}
- estimator: 'mle' | 'eap' (default 'mle')
- prior: optional {mean: float, sd: float} for EAP
- scaling: optional {A: float, B: float} => scaled_score = round(A*theta + B)

Outputs (dict):
- theta, se, ci: {low, high, level}
- scaled_score (optional), percentile (approx, Normal CDF)
- topic_breakdown: {topic: {n, correct, pct}}
- items_review: list of {id, correct, time_spent_sec, solution(optional)}
- recommendations: list of strings (topics to review)
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Mapping, Sequence

from .adaptive import sem_from_items

# Import from shared.irt module (irt.py), not irt/ package
# Need to use importlib to load the .py file explicitly due to name conflict with irt/ directory
import importlib.util
_spec = importlib.util.spec_from_file_location("shared.irt_module", __file__.replace("reporting.py", "irt.py"))
if _spec and _spec.loader:
    _irt_module = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(_irt_module)
else:
    raise ImportError("Cannot load shared.irt module")

eap_theta = _irt_module.eap_theta
mle_theta_fisher = _irt_module.mle_theta_fisher


def _norm_cdf(x: float) -> float:
    """Standard Normal CDF using erf."""
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def _to_bool(x: Any) -> bool:
    if isinstance(x, bool):
        return x
    try:
        return bool(int(x))
    except Exception:
        return False


def _irt_items(items: Sequence[Mapping]) -> List[Dict[str, float]]:
    out: List[Dict[str, float]] = []
    for it in items:
        out.append(
            {
                "a": float(it.get("a", 1.0)),
                "b": float(it.get("b", 0.0)),
                "c": float(it.get("c", 0.0)),
            }
        )
    return out


def _responses(items: Sequence[Mapping]) -> List[int]:
    ys: List[int] = []
    for it in items:
        ys.append(1 if _to_bool(it.get("correct", False)) else 0)
    return ys


def _topic_breakdown(items: Sequence[Mapping]) -> Dict[str, Dict[str, float]]:
    stats: Dict[str, Dict[str, float]] = {}
    for it in items:
        topic = it.get("topic")
        if topic is None:
            topic = "(unknown)"
        topic = str(topic)
        st = stats.setdefault(topic, {"n": 0.0, "correct": 0.0, "pct": 0.0})
        st["n"] += 1.0
        if _to_bool(it.get("correct", False)):
            st["correct"] += 1.0
    for st in stats.values():
        n = max(st.get("n", 0.0), 1.0)
        st["pct"] = float(st.get("correct", 0.0)) / n
    return stats


def _recommendations(topic_stats: Mapping[str, Mapping[str, float]], top_k: int = 3) -> List[str]:
    # Sort by ascending pct correct, require at least 2 items to be confident
    candidates = [
        (topic, st.get("pct", 0.0), st.get("n", 0.0))
        for topic, st in topic_stats.items()
    ]
    candidates.sort(key=lambda t: (t[1], t[2]))
    recs: List[str] = []
    for topic, pct, n in candidates:
        if n >= 2 and pct <= 0.7:
            recs.append(f"Review topic '{topic}' (accuracy {pct:.0%}, n={int(n)})")
        if len(recs) >= top_k:
            break
    return recs


def generate_report(payload: Mapping[str, Any]) -> Dict[str, Any]:
    items = list(payload.get("items", []))
    if not items:
        raise ValueError("items required")

    estimator = str(payload.get("estimator", "mle")).lower()
    prior = payload.get("prior") or {}
    scaling = payload.get("scaling") or {}

    its = _irt_items(items)
    ys = _responses(items)

    # Estimate theta
    if estimator == "eap":
        theta = eap_theta(
            its,
            ys,
            prior_mean=float(prior.get("mean", 0.0)),
            prior_sd=float(prior.get("sd", 1.0)),
        )
    else:
        theta = mle_theta_fisher(its, ys, initial_theta=0.0)

    # SE and CI
    se = sem_from_items(theta, its) if its else float("inf")
    z = 1.96
    ci = {"low": theta - z * se, "high": theta + z * se, "level": 0.95}

    # Scaled score and percentile
    scaled_score = None
    if "A" in scaling or "B" in scaling:
        A = float(scaling.get("A", 100.0))
        B = float(scaling.get("B", 500.0))
        scaled_score = int(round(A * theta + B))
    percentile = _norm_cdf(theta)

    # Topics and item review
    topic_stats = _topic_breakdown(items)
    items_review = [
        {
            "id": it.get("id"),
            "correct": _to_bool(it.get("correct", False)),
            "time_spent_sec": int(it.get("time_spent_sec", 0) or 0),
            "solution": it.get("solution"),
            "topic": it.get("topic"),
        }
        for it in items
    ]
    recs = _recommendations(topic_stats)

    report: Dict[str, Any] = {
        "theta": theta,
        "se": se,
        "ci": ci,
        "percentile": percentile,
        "topic_breakdown": topic_stats,
        "items_review": items_review,
        "recommendations": recs,
    }
    if scaled_score is not None:
        report["scaled_score"] = scaled_score

    return report
