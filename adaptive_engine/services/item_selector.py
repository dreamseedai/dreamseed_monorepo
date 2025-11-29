import random
from typing import Dict, List, Optional, Set

from adaptive_engine.utils.irt_math import fisher_information


def select_next_question(
    theta: float,
    available_questions: List[Dict],
    seen_ids: List[int | str],
    topic_counts: Optional[Dict[str, int]] = None,
    max_per_topic: Optional[int] = None,
    prefer_balanced: bool = True,
    deterministic: bool = False,
    top_k_random: Optional[int] = None,
    avoid_topic: Optional[str] = None,
    info_band_fraction: float = 0.05,
    exclude_ids: Optional[Set[str | int]] = None,
) -> Optional[Dict]:
    """
    Information-max selection with optional topic balancing and exposure controls.

    - Exclude seen_ids
    - Score by Fisher info at theta
    - If prefer_balanced, apply a small penalty to overrepresented topics
    - Honor max_per_topic exposure if provided
    - Deterministic mode: select the best by stable sort
    """
    seen = set(seen_ids)
    ex = exclude_ids or set()
    ex_str = {str(x) for x in ex}
    candidates = [
        q
        for q in available_questions
        if q.get("question_id") not in seen and str(q.get("question_id")) not in ex_str
    ]
    if not candidates:
        return None

    tcounts = topic_counts or {}

    def topic_of(q: Dict) -> str:
        return str(q.get("topic") or q.get("topic_name") or "General")

    # Apply max_per_topic exposure filter
    if max_per_topic is not None:
        filtered = []
        for q in candidates:
            t = topic_of(q)
            if tcounts.get(t, 0) < max_per_topic:
                filtered.append(q)
        if filtered:
            candidates = filtered

    # Score candidates
    scored = []
    for q in candidates:
        a = float(q.get("a", 1.0) or 1.0)
        b = float(q.get("b", 0.0) or 0.0)
        c = float(q.get("c", 0.2) or 0.2)
        info = fisher_information(theta, a, b, c)
        score = info
        if prefer_balanced:
            # penalize topics already seen more often
            t = topic_of(q)
            score *= 1.0 / (1.0 + 0.1 * tcounts.get(t, 0))
        scored.append({"question": q, "score": score})

    scored.sort(key=lambda x: x["score"], reverse=True)
    if deterministic:
        pick = scored[0]["question"]
    else:
        if top_k_random and top_k_random > 0:
            pool = [x["question"] for x in scored[: min(top_k_random, len(scored))]]
        else:
            top_score = scored[0]["score"]
            band = info_band_fraction * max(1.0, top_score)
            pool = [
                x["question"] for x in scored if abs(x["score"] - top_score) <= band
            ]
        pool = pool or [scored[0]["question"]]
        # Avoid same topic as last when a viable alternative exists
        if avoid_topic:
            alt = [
                q
                for q in pool
                if (q.get("topic") or q.get("topic_name")) != avoid_topic
            ]
            pool = alt or pool
        pick = random.choice(pool)
    return pick
