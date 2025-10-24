"""SeedTest API adaptive selection adapter.

Bridges the repository's question schema to the shared IRT/adaptive utilities.

Assumed item schema keys (from DB rows or dicts):
  - question_id: identifier
  - discrimination: a (float)
  - difficulty: b (float)
  - guessing: c (float; optional)
  - topic_id: for pre-filtering
  - tags: list[str] or similar for pre-filtering
"""

from __future__ import annotations

from typing import Iterable, Mapping, Optional, Sequence, Tuple

from shared.adaptive import KeyMap, choose_next_item, run_adaptive_session

# Default key mapping for the SeedTest questions schema
SEEDTEST_KEYMAP = KeyMap(id="question_id", a="discrimination", b="difficulty", c="guessing")


def _make_prefilter(topic_ids: Optional[Iterable[int]] = None, tags_any: Optional[Iterable[str]] = None):
    topics = set(topic_ids or [])
    tags = set(tags_any or [])
    if not topics and not tags:
        return None

    def _pred(it: Mapping) -> bool:
        if topics and it.get("topic_id") not in topics:
            return False
        if tags:
            t = it.get("tags") or []
            try:
                return bool(tags.intersection(set(t)))
            except Exception:
                return False
        return True

    return _pred


def choose_next_question(
    theta: float,
    items: Sequence[Mapping],
    used_ids: Optional[Iterable] = None,
    topic_ids: Optional[Iterable[int]] = None,
    tags_any: Optional[Iterable[str]] = None,
) -> Tuple[Mapping, float, int]:
    """Select the next question (max information) with optional topic/tags filters.

    Returns (original_item, info_value, index_in_input)
    """
    pre = _make_prefilter(topic_ids=topic_ids, tags_any=tags_any)
    return choose_next_item(theta, items, used_ids=used_ids, keymap=SEEDTEST_KEYMAP, prefilter=pre)


def simulate_adaptive_run(
    pool: Sequence[Mapping],
    true_theta: float,
    max_items: int = 5,
    sem_threshold: Optional[float] = None,
) -> Tuple[float, list]:
    """Run a tiny adaptive session over the pool using the SeedTest key mapping.

    Returns (estimated_theta, administered_ids)
    """
    return run_adaptive_session(
        pool,
        true_theta,
        max_items=max_items,
        sem_threshold=sem_threshold,
        keymap=SEEDTEST_KEYMAP,
    )


__all__ = [
    "SEEDTEST_KEYMAP",
    "choose_next_question",
    "simulate_adaptive_run",
]
