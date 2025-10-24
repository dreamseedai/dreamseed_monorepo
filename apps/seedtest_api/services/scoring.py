from __future__ import annotations

import math
from typing import Any, Dict, List, Tuple

from ..settings import Settings
from .adaptive_engine import fisher_information_3pl


# ------------------- Public helper functions -------------------

def raw_to_scaled(
    raw_score: float | int,
    max_score: float | int,
    *,
    scale_min: int = 0,
    scale_max: int = 200,
) -> int:
    """Linear scale raw to [scale_min, scale_max].

    If max_score <= 0, returns scale_min.
    """
    try:
        raw = float(raw_score)
        maxv = float(max_score)
        if maxv <= 0:
            return int(scale_min)
        pct = max(0.0, min(1.0, raw / maxv))
        val = int(round(scale_min + pct * (scale_max - scale_min)))
        return max(scale_min, min(scale_max, val))
    except Exception:
        return int(scale_min)


def theta_to_scaled(theta: float, *, mean: float = 100.0, sd: float = 50.0) -> int:
    """Map θ to a user-facing scale via linear transform and clip to [0,200]."""
    try:
        val = int(round(theta * sd + mean))
        return max(0, min(200, val))
    except Exception:
        return 0


def theta_to_percentile(theta: float) -> int:
    """Percentile under standard normal assumption for θ: Φ(θ)*100, clipped to [0,100]."""
    try:
        phi = 0.5 * (1.0 + math.erf(theta / math.sqrt(2.0)))
        return int(max(0, min(100, round(phi * 100.0))))
    except Exception:
        return 0


def topic_breakdown_from_responses(responses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    by_topic: Dict[str, Dict[str, int]] = {}
    for r in responses:
        t = str(r.get("topic") or "general")
        bucket = by_topic.setdefault(t, {"correct": 0, "total": 0})
        bucket["total"] += 1
        if r.get("correct"):
            bucket["correct"] += 1
    topics_list: List[Dict[str, Any]] = []
    for t, v in by_topic.items():
        acc = (v["correct"] / v["total"]) if v["total"] else 0.0
        topics_list.append(
            {
                "topic": t,
                "correct": v["correct"],
                "total": v["total"],
                "accuracy": round(acc, 3),
            }
        )
    return topics_list


def derive_recommendations(
    topics_list: List[Dict[str, Any]], *, weakness_threshold: float = 0.60
) -> Tuple[List[str], List[str], List[str]]:
    """Return (strengths, weaknesses, recommendations) from topic stats."""
    strengths = sorted(
        [x["topic"] for x in topics_list if float(x.get("accuracy") or 0.0) >= 0.75]
    )[:3]
    weaknesses = sorted(
        [x["topic"] for x in topics_list if float(x.get("accuracy") or 0.0) <= weakness_threshold]
    )[:3]
    recs: List[str] = [
        f"{w} 영역의 정답률이 낮습니다. 교과서 핵심 개념을 복습하고 관련 문제 풀이를 늘려보세요."
        for w in weaknesses
    ]
    return strengths, weaknesses, recs


def aggregate_from_session_state(state: Dict[str, Any] | None) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """Compute a simple result JSON and topic breakdown from a session "state" dict.

    The state is expected to contain a list at key "responses", where each item may have:
    - question_id, topic (optional), correct (bool), a/b/c (IRT params), answer
    """
    if not state or not isinstance(state.get("responses"), list):
        return {
            "score": {"raw": 0, "scaled": 0},
            "topics": [],
            "summary": {"strengths": [], "weaknesses": []},
            "recommendations": [],
            "questions": [],
            "metadata": {"version": "v1"},
            "ability_estimate": 0.0,
            "standard_error": None,
            "percentile": None,
        }, []

    responses: List[Dict[str, Any]] = state["responses"]
    total = len(responses)
    correct = sum(1 for r in responses if bool(r.get("correct")))

    # Ability (theta) from adaptive engine if present
    theta_val = state.get("theta", None)
    theta = float(theta_val) if isinstance(theta_val, (int, float)) else None

    # Scaled score via helpers
    if theta is not None:
        scaled = theta_to_scaled(theta)
    else:
        # Map percent-correct to 0..100 scale to match public contract expectations
        scaled = raw_to_scaled(correct, max(total, 1), scale_min=0, scale_max=100)

    # Topic breakdown (best-effort; default topic="general")
    topics_list = topic_breakdown_from_responses(responses)

    # Simple strengths/weaknesses
    strengths, weaknesses, recs = derive_recommendations(topics_list, weakness_threshold=0.60)

    # Build questions array for UI consumption
    questions: List[Dict[str, Any]] = []
    for r in responses:
        questions.append({
            "question_id": r.get("question_id"),
            "is_correct": bool(r.get("correct")),
            "user_answer": r.get("answer"),
            "correct_answer": r.get("correct_answer"),
            "explanation": r.get("explanation"),
            "topic": r.get("topic") or "general",
        })

    # Standard error approximation via total Fisher information at final theta
    se: float | None = None
    if theta is not None:
        try:
            I_total = 0.0
            for r in responses:
                a = float(r.get("a") or 1.0)
                b = float(r.get("b") or 0.0)
                c = float(r.get("c") or 0.2)
                I_total += float(fisher_information_3pl(a, b, c, theta))
            # Add prior information 1/sigma^2 if using Bayesian prior
            s = Settings()
            prior_var = float(s.CAT_PRIOR_SD or 1.0) ** 2
            I_total += (1.0 / prior_var)
            if I_total > 0:
                se = float(1.0 / math.sqrt(I_total))
        except Exception:
            se = None

    # Percentile under standard normal assumption for theta
    pct: int | None = None
    if theta is not None:
        try:
            pct = theta_to_percentile(theta)
        except Exception:
            pct = None

    result_json = {
        "score": {"raw": correct, "scaled": scaled},
        "topics": topics_list,
        "summary": {"strengths": strengths, "weaknesses": weaknesses},
        "recommendations": recs,
        "questions": questions,
        "metadata": {"version": "v1"},
        "ability_estimate": theta if theta is not None else 0.0,
        "standard_error": se,
        "percentile": pct,
    }
    return result_json, topics_list
