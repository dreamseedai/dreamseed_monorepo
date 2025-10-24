import os
import sys
from pathlib import Path

# Ensure LOCAL_DEV and import path
os.environ.setdefault("LOCAL_DEV", "true")
PACKAGE_PARENT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE_PARENT))

import seedtest_api.routers.results as results_mod  # type: ignore


def test_to_contract_response_uses_top_level_scores():
    src = {
        "session_id": "sess-1",
        "status": "ready",
        "score_raw": 34.0,
        "score_scaled": 128.5,
        "topics": [],
    }
    out = results_mod._to_contract_response(src, fallback_session_id="sess-1")
    assert out["score"] == 128.5
    assert out["score_detail"] == {"raw": 34.0, "scaled": 128.5}


def test_to_contract_response_uses_nested_score_when_top_level_missing():
    src = {
        "session_id": "sess-2",
        "status": "ready",
        "score": {"raw": 30.0, "scaled": 120.0},
        "topics": [],
    }
    out = results_mod._to_contract_response(src, fallback_session_id="sess-2")
    assert out["score"] == 120.0
    assert out["score_detail"] == {"raw": 30.0, "scaled": 120.0}


def test_percentile_and_accuracy_bounds_validation():
    from datetime import datetime, timezone

    from pydantic import ValidationError
    from seedtest_api.schemas.result import ResultContract, ScoreDetail, TopicBreakdown

    # Valid case should pass
    valid = ResultContract(
        exam_session_id="s",
        user_id="u",
        exam_id=1,
        score=100.0,
        score_detail=ScoreDetail(raw=30.0, scaled=100.0),
        percentile=85,
        topic_breakdown=[TopicBreakdown(topic="t", correct=1, total=2, accuracy=0.5)],
        questions=[],
        recommendations=[],
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        status="ready",
    )
    assert valid.percentile == 85

    # Invalid percentile (<0)
    try:
        ResultContract(
            exam_session_id="s",
            score=100.0,
            score_detail=ScoreDetail(raw=None, scaled=100.0),
            percentile=-1,
            topic_breakdown=[],
            questions=[],
            recommendations=[],
            created_at=None,
            updated_at=None,
            status="ready",
        )
        assert False, "Expected ValidationError for percentile < 0"
    except ValidationError:
        pass

    # Invalid accuracy (>1)
    try:
        ResultContract(
            exam_session_id="s",
            score=100.0,
            score_detail=ScoreDetail(raw=None, scaled=100.0),
            percentile=50,
            topic_breakdown=[
                TopicBreakdown(topic="t", correct=1, total=1, accuracy=1.5)
            ],
            questions=[],
            recommendations=[],
            created_at=None,
            updated_at=None,
            status="ready",
        )
        assert False, "Expected ValidationError for accuracy > 1"
    except ValidationError:
        pass


def test_updated_at_in_mapper():
    from datetime import datetime, timezone

    ts = datetime(2025, 10, 18, 10, 0, 0, tzinfo=timezone.utc)
    src = {
        "session_id": "sess-3",
        "status": "ready",
        "score_raw": 10.0,
        "score_scaled": 50.0,
        "updated_at": ts,
    }
    out = results_mod._to_contract_response(src, fallback_session_id="sess-3")
    assert out["updated_at"] == "2025-10-18T10:00:00+00:00".replace("+00:00", "Z")
