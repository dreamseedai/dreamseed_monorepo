import os

from ..services.loader import build_loader_filters
from ..settings import settings


def test_build_loader_filters_env_example(tmp_path, monkeypatch):
    # Simulate env like .env.example
    monkeypatch.setenv("BANK_ORG_ID", "1001")
    monkeypatch.setenv("BANK_SUBJECT", "MATH")
    monkeypatch.setenv("BANK_DIFF_MIN", "-1.0")
    monkeypatch.setenv("BANK_DIFF_MAX", "1.0")
    monkeypatch.setenv("BANK_TOPIC_IDS", "10, 12 15")
    monkeypatch.setenv("BANK_TAGS", "algebra, geometry proof")
    monkeypatch.setenv("BANK_SAMPLE_K", "50")
    monkeypatch.setenv("TAGS_KIND_TTL_SEC", "300")

    # Reload settings by creating a new instance if needed
    from ..settings import Settings

    s = Settings()
    assert s.BANK_ORG_ID == 1001
    assert s.BANK_SUBJECT == "MATH"
    assert s.BANK_DIFF_MIN == -1.0
    assert s.BANK_DIFF_MAX == 1.0
    assert s.bank_topic_ids == [10, 12, 15]
    assert s.bank_tags == ["algebra", "geometry", "proof"]
    assert s.BANK_SAMPLE_K == 50
    assert s.TAGS_KIND_TTL_SEC == 300

    filters = build_loader_filters()
    assert filters["org_id"] == 1001
    assert filters["subject"] == "MATH"
    assert filters["diff_min"] == -1.0
    assert filters["diff_max"] == 1.0
    assert filters["topics"] == [10, 12, 15]
    assert filters["tags"] == ["algebra", "geometry", "proof"]
    assert filters["sample_k"] == 50
    assert filters["sample_p"] is None
    assert filters["tags_kind_ttl_sec"] == 300
