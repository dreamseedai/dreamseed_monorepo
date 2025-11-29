from typing import Dict, List, Union, Optional, Any
import math


def generate_feedback(
    responses: List[Dict], questions: Union[Dict, List[Dict]]
) -> List[str]:
    """Generate topic-level feedback messages based on correctness rates."""
    topic_summary: Dict[str, Dict[str, int]] = {}
    for r in responses:
        q = questions.get(r["question_id"]) if isinstance(questions, dict) else None
        if not q:
            # If questions is a list, try to find by id
            if isinstance(questions, list):
                q = next(
                    (
                        x
                        for x in questions
                        if x.get("question_id") == r.get("question_id")
                    ),
                    None,
                )
        if not q:
            # Unknown question, skip
            continue
        topic = q.get("topic_name") or q.get("topic") or "General"
        stats = topic_summary.setdefault(topic, {"correct": 0, "total": 0})
        stats["total"] += 1
        if r.get("is_correct"):
            stats["correct"] += 1

    feedback: List[str] = []
    for topic, stats in topic_summary.items():
        total = max(1, stats["total"])  # avoid zero-division
        rate = stats["correct"] / total
        msg = f"{topic}: 정답률 {rate:.0%} "
        msg += "→ 보완 필요" if rate < 0.6 else "→ 양호"
        feedback.append(msg)
    return feedback


def _ensure_qmap(questions: Union[Dict, List[Dict]]) -> Dict[str, Dict[str, Any]]:
    if isinstance(questions, dict):
        return {str(k): v for k, v in questions.items()}
    return {str(q.get("question_id")): q for q in questions}


def _topic_of(q: Dict[str, Any]) -> str:
    return str(q.get("topic_name") or q.get("topic") or "General")


def _explanation_of(q: Dict[str, Any]) -> Optional[str]:
    # Look for common explanation keys
    for key in ("solution_explanation", "explanation", "solution"):
        val = q.get(key)
        if isinstance(val, str) and val.strip():
            return val
    return None


def _normal_percentile(theta: float) -> float:
    # Percentile under N(0,1)
    return 50.0 * (1.0 + math.erf(float(theta) / math.sqrt(2.0)))


def generate_detailed_feedback(
    responses: List[Dict],
    questions: Union[Dict, List[Dict]],
    theta: Optional[float] = None,
    se: Optional[float] = None,
    scaled_score: Optional[float] = None,
) -> Dict[str, Any]:
    """Generate a structured feedback report.

    Returns keys:
      - summary: { theta, se, percentile, scaled_score }
      - items_review: [{ question_id, correct, topic, explanation? }]
      - topic_breakdown: { topic: { correct, total, accuracy } }
      - recommendations: [str]
    """
    qmap = _ensure_qmap(questions)
    # Build per-item review
    items_review: List[Dict[str, Any]] = []
    topic_summary: Dict[str, Dict[str, float]] = {}
    for r in responses:
        qid = str(r.get("question_id"))
        q = qmap.get(qid) or {}
        topic = _topic_of(q)
        correct = bool(r.get("is_correct"))
        items_review.append(
            {
                "question_id": qid,
                "correct": correct,
                "topic": topic,
                "explanation": _explanation_of(q),
            }
        )
        stats = topic_summary.setdefault(topic, {"correct": 0.0, "total": 0.0})
        stats["total"] += 1.0
        if correct:
            stats["correct"] += 1.0
    # Compute accuracies
    topic_breakdown: Dict[str, Dict[str, float]] = {}
    for t, s in topic_summary.items():
        total = max(1.0, float(s["total"]))
        acc = float(s["correct"]) / total
        topic_breakdown[t] = {
            "correct": float(s["correct"]),
            "total": float(s["total"]),
            "accuracy": acc,
        }
    # Recommendations: topics below 60% accuracy
    recommendations: List[str] = []
    weak = sorted([t for t, s in topic_breakdown.items() if s["accuracy"] < 0.6])
    for t in weak:
        pct = topic_breakdown[t]["accuracy"] * 100.0
        recommendations.append(
            f"'{t}' 영역 정답률 {pct:.0f}%. 핵심 개념 복습과 유사 문항 추가 연습을 권장합니다."
        )
    # Summary with percentile
    percentile: Optional[float] = None
    if theta is not None:
        percentile = _normal_percentile(theta)

    return {
        "summary": {
            "theta": theta,
            "se": se,
            "percentile": percentile,
            "scaled_score": scaled_score,
        },
        "items_review": items_review,
        "topic_breakdown": topic_breakdown,
        "recommendations": recommendations,
    }
