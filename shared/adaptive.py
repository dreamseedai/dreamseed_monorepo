"""Adaptive testing utilities built on top of shared.irt.

Provides:
- SEM estimator from item information
- Schema-adapting choose_next_item that maps arbitrary item dicts to (id,a,b,c)
- Optional NumPy-accelerated information scoring for large pools
- A tiny helper to run a short adaptive session loop (for tests/demos)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import (
    Callable,
    Dict,
    Iterable,
    List,
    Mapping,
    Optional,
    Sequence,
    Tuple,
)

try:  # optional dependency; code paths guarded
    import importlib.util as _util
    _HAS_NUMPY = _util.find_spec("numpy") is not None
except Exception:  # pragma: no cover
    _HAS_NUMPY = False

# Import from shared.irt module (irt.py), not irt/ package
# Need to use importlib to load the .py file explicitly due to name conflict with irt/ directory
import importlib.util
_spec = importlib.util.spec_from_file_location("shared.irt_module", __file__.replace("adaptive.py", "irt.py"))
if _spec and _spec.loader:
    _irt_module = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(_irt_module)
else:
    raise ImportError("Cannot load shared.irt module")

irf_3pl = _irt_module.irf_3pl
item_information_3pl = _irt_module.item_information_3pl

try:  # noqa: E402 - after import of irt
    item_information_batch_np = _irt_module.item_information_batch_np  # type: ignore
except Exception:  # pragma: no cover
    item_information_batch_np = None  # type: ignore


def sem_from_items(theta: float, items: Sequence[Mapping]) -> float:
    """Standard Error of Measurement (SEM) from total Fisher Information.

    SEM ≈ 1 / sqrt(I_total), where I_total = Σ I_i(θ).
    Returns float('inf') if total information is ~0.
    Each mapping must provide keys a,b, optional c.
    """
    i_total = 0.0
    for it in items:
        a = float(it["a"])
        b = float(it["b"])
        c = float(it.get("c", 0.0))
        i_total += item_information_3pl(theta, a, b, c)
    if i_total <= 1e-12:
        return float("inf")
    return (1.0 / i_total) ** 0.5


@dataclass(frozen=True)
class KeyMap:
    id: str = "id"
    a: str = "a"
    b: str = "b"
    c: str = "c"


def _map_item(it: Mapping, km: KeyMap) -> Dict:
    return {
        "id": it.get(km.id),
        "a": float(it[km.a]),
        "b": float(it[km.b]),
        "c": float(it.get(km.c, 0.0)),
        "_raw": it,
    }


def choose_next_item(
    theta: float,
    items: Sequence[Mapping],
    used_ids: Optional[Iterable] = None,
    keymap: Optional[KeyMap] = None,
    prefilter: Optional[Callable[[Mapping], bool]] = None,
) -> Tuple[Mapping, float, int]:
    """Choose next item by maximum information at ability theta.

    - items: sequence of mappings; fields are mapped via keymap (default id,a,b,c)
    - used_ids: iterable of IDs to exclude
    - prefilter: optional predicate to include only eligible items (e.g., by topic/tag)

    Returns (original_item, info_value, index_in_input)
    """
    used = set(used_ids or [])
    km = keymap or KeyMap()

    # Filter and map
    cand_idx: List[int] = []
    mapped: List[Dict] = []
    for idx, it in enumerate(items):
        if prefilter and not prefilter(it):
            continue
        mid = it.get(km.id)
        if mid in used:
            continue
        mapped.append(_map_item(it, km))
        cand_idx.append(idx)

    if not mapped:
        raise ValueError("No selectable items after filtering/used_ids")

    # Score information (NumPy fast path when available)
    if _HAS_NUMPY and item_information_batch_np is not None:  # type: ignore
        infos_arr = item_information_batch_np(theta, mapped)  # type: ignore
        best_local = int(infos_arr.argmax())
        best_info = float(infos_arr[best_local])
    else:
        best_local = -1
        best_info = -1.0
        for j, it in enumerate(mapped):
            info = item_information_3pl(theta, it["a"], it["b"], it.get("c", 0.0))
            if info > best_info:
                best_info = info
                best_local = j

    global_idx = cand_idx[best_local]
    return items[global_idx], best_info, global_idx


def _topic_of(it: Mapping, topic_key: str) -> Optional[object]:  # pragma: no cover (helper)
    try:
        return it.get(topic_key)  # type: ignore[attr-defined]
    except Exception:
        return None


def select_next_with_constraints(
    theta: float,
    items: Sequence[Mapping],
    used_ids: Optional[Iterable] = None,
    *,
    keymap: Optional[KeyMap] = None,
    prefilter: Optional[Callable[[Mapping], bool]] = None,
    top_n: int = 1,
    exposure_counts: Optional[Mapping] = None,
    max_exposure: Optional[int] = None,
    acceptance_probs: Optional[Mapping] = None,
    last_topics: Optional[Sequence] = None,
    topic_key: str = "topic_id",
    avoid_repeat_k: int = 2,
    repeat_penalty: float = 0.15,
    content_blueprint: Optional[Mapping] = None,
    content_counts: Optional[Mapping] = None,
    avoid_same_topic_hard: bool = False,
    same_topic_tolerance: float = 0.05,
    default_acceptance_p: Optional[float] = None,
) -> Tuple[Mapping, float, int]:
    """Select next item using information with exposure/content constraints.

    - Randomesque: randomly choose among top_n by adjusted weights
    - Exposure control: skip items over max_exposure; optionally apply Sympson-Hetter acceptance_probs
    - Content balancing: apply penalty for repeating last topic too often; boost underrepresented topics
    """
    used = set(used_ids or [])
    km = keymap or KeyMap()

    # Stage 1: filter and compute base information
    scored: List[Tuple[int, Mapping, float]] = []  # (index, item, info)
    for idx, it in enumerate(items):
        if prefilter and not prefilter(it):
            continue
        iid = it.get(km.id)
        if iid in used:
            continue
        # Exposure hard cap
        if max_exposure is not None and exposure_counts is not None:
            if exposure_counts.get(iid, 0) >= max_exposure:  # type: ignore[index]
                continue
        a = float(it[km.a])
        b = float(it[km.b])
        c = float(it.get(km.c, 0.0))
        info = item_information_3pl(theta, a, b, c)
        scored.append((idx, it, info))

    if not scored:
        raise ValueError("No selectable items after constraints")

    # Stage 2: sort by base info
    scored.sort(key=lambda t: t[2], reverse=True)

    # Stage 3: apply content penalties/boosts to form adjusted weights
    weights: List[Tuple[int, Mapping, float, float]] = []  # (idx, item, base_info, weight)
    recent_topics = list(last_topics or [])[-max(avoid_repeat_k, 0):]
    for idx, it, base_info in scored[: max(top_n, 1)]:
        topic = _topic_of(it, topic_key)
        # Penalty for repeating same topic as recent ones
        penalty = 0.0
        if avoid_repeat_k > 0 and topic is not None and topic in recent_topics:
            # Cap to [0, 0.9] for safety
            penalty = min(max(float(repeat_penalty), 0.0), 0.9)

        # Blueprint boost for underrepresented topics
        boost = 0.0
        if content_blueprint and content_counts and topic in content_blueprint:
            target = float(content_blueprint.get(topic, 0.0))
            achieved = float(content_counts.get(topic, 0.0))
            gap = max(target - achieved, 0.0)
            if target > 0:
                # Boost up to +20% when gap is large
                boost = min(0.2, 0.2 * (gap / max(target, 1e-9)))

        weight = base_info * (1.0 - penalty) * (1.0 + boost)
        weights.append((idx, it, base_info, weight))

    # Stage 4: Sympson-Hetter acceptance per item (probabilistic gate)
    import random

    def accepted(iid) -> bool:
        p = 1.0
        if acceptance_probs is not None:
            p = float(acceptance_probs.get(iid, p))  # type: ignore[index]
        if default_acceptance_p is not None:
            p = min(p, float(default_acceptance_p))
        return random.random() < max(min(p, 1.0), 0.0)

    # Stage 5: randomesque selection among top_n using weights
    # normalize weights; if all zero, fallback to base_info
    total_w = sum(max(w, 0.0) for _, _, _, w in weights)
    if total_w <= 0:
        total_w = sum(b for _, _, b, _ in weights) or 1.0
        weights = [(i, it, b, b) for (i, it, b, _) in weights]

    r = random.random() * total_w
    acc = 0.0
    chosen = weights[0]
    for triple in weights:
        acc += triple[3]
        if r <= acc:
            chosen = triple
            break

    idx, it, base_info, w = chosen
    iid = it.get(km.id)
    # Apply Sympson-Hetter acceptance; if rejected, fall back to next weight order
    if not accepted(iid):
        # pick next best that is accepted
        for triple in sorted(weights, key=lambda t: t[3], reverse=True):
            i2, it2, base2, w2 = triple
            if accepted(it2.get(km.id)):
                idx, it, base_info = i2, it2, base2
                break

    # Hard avoid same topic as last if configured, unless information advantage exceeds tolerance
    if avoid_same_topic_hard and last_topics:
        last = last_topics[-1]
        topic_cur = _topic_of(it, topic_key)
        if topic_cur is not None and last is not None and topic_cur == last and len(weights) > 1:
            # Find best alternative with different topic
            alt = None
            for i2, it2, base2, w2 in sorted(weights, key=lambda t: t[3], reverse=True):
                if _topic_of(it2, topic_key) != last:
                    alt = (i2, it2, base2, w2)
                    break
            if alt is not None:
                _, _, alt_info, _ = alt
                # If current base_info <= (1 + tol) * alt_info, switch to alternative
                tol = max(same_topic_tolerance, 0.0)
                if base_info <= (1.0 + tol) * alt_info:
                    idx, it, base_info = alt[0], alt[1], alt[2]

    return items[idx], base_info, idx


def run_adaptive_session(
    pool: Sequence[Mapping],
    true_theta: float,
    max_items: int = 5,
    sem_threshold: Optional[float] = None,
    estimator: str = "mle",
    keymap: Optional[KeyMap] = None,
) -> Tuple[float, List[int]]:
    """Run a tiny, deterministic adaptive loop for demos/tests.

    - Uses deterministic pseudo responses: y = 1 if P >= 0.5 else 0.
    - Re-estimates θ after each item using MLE or EAP.
    Returns (estimated_theta, administered_ids)
    """
    from .irt import eap_theta, irf_3pl, mle_theta_fisher  # type: ignore

    theta = 0.0
    used_ids: List = []
    asked: List[dict] = []
    answers: List[int] = []
    km = keymap or KeyMap()

    for _ in range(max_items):
        item, info, idx = choose_next_item(theta, pool, used_ids=used_ids, keymap=km)
        mid = item.get(km.id)
        if mid is not None:
            used_ids.append(mid)
        asked.append({
            "a": float(item[km.a]),
            "b": float(item[km.b]),
            "c": float(item.get(km.c, 0.0)),
        })
        p = irf_3pl(true_theta, asked[-1]["a"], asked[-1]["b"], asked[-1]["c"])
        y = int(p >= 0.5)
        answers.append(y)

        if estimator == "mle":
            theta = mle_theta_fisher(asked, answers, initial_theta=theta)
        else:
            theta = eap_theta(asked, answers, prior_mean=0.0, prior_sd=1.0)
        # Clamp theta to a reasonable range to avoid divergence in tiny demo loops
        if theta > 4.0:
            theta = 4.0
        elif theta < -4.0:
            theta = -4.0

        if sem_threshold is not None:
            sem = sem_from_items(theta, asked)
            if sem <= sem_threshold:
                break

    return theta, used_ids


__all__ = [
    "KeyMap",
    "sem_from_items",
    "choose_next_item",
    "run_adaptive_session",
]


# ----------------------------
# Stopping rule helper
# ----------------------------

def evaluate_stop(
    theta: float,
    asked_items: Sequence[Mapping],
    *,
    min_items: int = 1,
    max_items: Optional[int] = None,
    sem_threshold: Optional[float] = None,
    start_time_seconds: Optional[float] = None,
    max_time_seconds: Optional[float] = None,
) -> tuple[bool, str, float]:
    """Evaluate if an adaptive test should stop.

    Criteria (checked in this order):
    - max_items reached
    - time exceeded (if provided)
    - after at least min_items, SEM <= sem_threshold (if provided)

    Returns (should_stop, reason, sem_value)
    """
    n = len(asked_items)
    sem_val = sem_from_items(theta, asked_items) if asked_items else float("inf")

    if max_items is not None and n >= max_items:
        return True, "max_items", sem_val

    if max_time_seconds is not None and start_time_seconds is not None:
        import time

        if (time.time() - start_time_seconds) >= max_time_seconds:
            return True, "max_time", sem_val

    if sem_threshold is not None and n >= min_items and sem_val <= sem_threshold:
        return True, "sem_threshold", sem_val

    return False, "continue", sem_val

