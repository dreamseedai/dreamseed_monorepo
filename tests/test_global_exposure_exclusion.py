import types

import pytest

from adaptive_engine.models.schemas import NextRequest, Question


def test_next_question_excludes_overexposed(monkeypatch):
    # Arrange: two items where 'B' would normally be stronger (higher 'a'),
    # but it is flagged as globally overexposed and must be excluded.
    payload = NextRequest(
        theta=0.0,
        available_questions=[
            Question(question_id="A", a=1.0, b=0.0, c=0.2, topic="T1"),
            Question(question_id="B", a=2.0, b=0.0, c=0.2, topic="T1"),
        ],
        # Non-empty seen_ids to bypass first-item heuristic path in the router
        seen_ids=["init"],
    )

    # Stub settings to enable exposure exclusion
    from adaptive_engine import config as cfg

    settings = cfg.AppSettings(
        exposure_max_per_window=1,
        exposure_window_hours=24,
    )
    monkeypatch.setattr(cfg, "get_settings", lambda: settings, raising=True)

    # Force deterministic selection so we can assert exact item
    monkeypatch.setattr(
        cfg,
        "get_selection_policy",
        lambda: cfg.SelectionPolicy(prefer_balanced=False, deterministic=True, max_per_topic=None, top_k_random=None, info_band_fraction=0.05),
        raising=True,
    )

    # Stub global overexposed set to contain 'B'
    # Act: patch the symbol used inside the router module for robust behavior
    import adaptive_engine.routers.exam_session as exam_router
    monkeypatch.setattr(exam_router, "get_overexposed_question_ids", lambda threshold, window: {"B"}, raising=True)

    resp = exam_router.get_next_question(payload)

    # Assert
    assert resp.question is not None
    assert resp.question.question_id == "A"
