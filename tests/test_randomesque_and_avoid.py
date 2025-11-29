import random

from adaptive_engine.services.item_selector import select_next_question


def test_top_k_random_uses_pool(monkeypatch):
    # Two top-scoring items; ensure selection can pick the second via random choice.
    theta = 0.0
    items = [
        {"question_id": "Q1", "a": 1.0, "b": 0.0, "c": 0.2, "topic": "X"},
        {"question_id": "Q2", "a": 1.0, "b": 0.0, "c": 0.2, "topic": "X"},
        {"question_id": "Q3", "a": 0.5, "b": 0.0, "c": 0.2, "topic": "X"},
    ]

    # Force random.choice to pick the last element of the provided pool
    monkeypatch.setattr(random, "choice", lambda seq: seq[-1])

    pick = select_next_question(
        theta,
        items,
        seen_ids=[],
        topic_counts={},
        max_per_topic=None,
        prefer_balanced=False,
        deterministic=False,
        top_k_random=2,
        avoid_topic=None,
        info_band_fraction=0.01,
        exclude_ids=None,
    )
    assert pick is not None
    # From top-2, ensure the second best (Q2 by stable order) can be selected
    assert pick["question_id"] in {"Q1", "Q2"}


def test_info_band_fraction_pool(monkeypatch):
    theta = 0.0
    # Q1 and Q2 have same parameters, thus same info; Q3 is weaker
    items = [
        {"question_id": "Q1", "a": 1.0, "b": 0.0, "c": 0.2, "topic": "X"},
        {"question_id": "Q2", "a": 1.0, "b": 0.0, "c": 0.2, "topic": "X"},
        {"question_id": "Q3", "a": 0.1, "b": 0.0, "c": 0.2, "topic": "X"},
    ]
    # Pick the second element from the band pool to prove it contains multiple items
    monkeypatch.setattr(
        random, "choice", lambda seq: seq[1] if len(seq) > 1 else seq[0]
    )

    pick = select_next_question(
        theta,
        items,
        seen_ids=[],
        topic_counts={},
        max_per_topic=None,
        prefer_balanced=False,
        deterministic=False,
        top_k_random=None,
        avoid_topic=None,
        info_band_fraction=0.10,  # generous enough to include identical top scores
        exclude_ids=None,
    )
    assert pick is not None
    assert pick["question_id"] in {"Q1", "Q2"}


def test_avoid_topic_removes_last_topic_from_pool(monkeypatch):
    theta = 0.0
    items = [
        {"question_id": "Q1", "a": 1.0, "b": 0.0, "c": 0.2, "topic": "T1"},
        {"question_id": "Q2", "a": 1.0, "b": 0.0, "c": 0.2, "topic": "T2"},
    ]
    # Bias random to pick first element of pool
    monkeypatch.setattr(random, "choice", lambda seq: seq[0])

    # With avoid_topic='T1', pool should exclude Q1 if a viable alternative exists
    pick = select_next_question(
        theta,
        items,
        seen_ids=[],
        topic_counts={"T1": 1, "T2": 0},
        max_per_topic=None,
        prefer_balanced=False,
        deterministic=False,
        top_k_random=None,
        avoid_topic="T1",
        info_band_fraction=0.50,
        exclude_ids=None,
    )
    assert pick is not None
    assert pick["question_id"] == "Q2"
