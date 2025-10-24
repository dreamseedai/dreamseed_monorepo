from __future__ import annotations

from typing import Any, Dict

from ..settings import Settings


def build_loader_filters() -> Dict[str, Any]:
    """Return normalized loader filters dict from env/settings.

    - topics: list[int]
    - tags: list[str]
    - org_id: int | None
    - subject: str | None
    - diff_min/diff_max: float | None
    - sample_k/sample_p: int | float | None
    """
    # Instantiate a fresh Settings so env var changes (e.g., in tests) are respected
    s = Settings()
    return {
        "org_id": s.BANK_ORG_ID,
        "subject": s.BANK_SUBJECT,
        "diff_min": s.BANK_DIFF_MIN,
        "diff_max": s.BANK_DIFF_MAX,
        "topics": s.bank_topic_ids,
        "tags": s.bank_tags,
        "sample_k": s.BANK_SAMPLE_K,
        "sample_p": s.BANK_SAMPLE_P,
        "tags_kind_ttl_sec": s.TAGS_KIND_TTL_SEC,
    }
