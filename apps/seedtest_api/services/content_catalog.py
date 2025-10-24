from __future__ import annotations
from typing import List, Optional, Any
import json
import os

from ..schemas.content import ContentItem, ContentSearchResult
from ..core.config import config

_CATALOG_CACHE: Optional[List[ContentItem]] = None


def _load_from_path(path: str) -> List[ContentItem]:
    data: Any
    with open(path, "r", encoding="utf-8") as f:
        txt = f.read()
    # Try JSON first
    try:
        data = json.loads(txt)
    except Exception:
        # Try YAML if pyyaml is available
        try:
            import yaml  # type: ignore

            data = yaml.safe_load(txt)
        except Exception as e:  # pragma: no cover - optional dep
            raise RuntimeError(f"Unsupported catalog format or parse error: {e}") from e
    items_raw = data.get("items") if isinstance(data, dict) else data
    if not isinstance(items_raw, list):
        raise RuntimeError("Catalog file must be a list or an object with 'items' list")
    out: List[ContentItem] = []
    for it in items_raw:
        try:
            out.append(ContentItem(**it))
        except Exception:
            continue
    return out


def _default_sample() -> List[ContentItem]:
    # Minimal embedded sample to make content-based recommender usable out-of-the-box
    raw = [
        {
            "id": "alg-vid-101",
            "title": "대수 기초 개념 정리 (영상)",
            "url": "https://example.com/algebra-basics",
            "topic_tags": ["대수", "algebra"],
            "difficulty": 2.0,
            "format": "video",
            "language": "ko",
            "provider": "ExampleEdu",
            "popularity_score": 0.8,
        },
        {
            "id": "prob-set-201",
            "title": "확률 기본 문제 세트 (연습)",
            "url": "https://example.com/probability-practice",
            "topic_tags": ["확률", "probability"],
            "difficulty": 3.0,
            "format": "problems",
            "language": "ko",
            "provider": "ExampleEdu",
            "popularity_score": 0.7,
        },
        {
            "id": "geom-article-150",
            "title": "기하 핵심 정리 (기사)",
            "url": "https://example.com/geometry-core",
            "topic_tags": ["기하", "geometry"],
            "difficulty": 3.5,
            "format": "article",
            "language": "ko",
            "provider": "ExampleEdu",
            "popularity_score": 0.6,
        },
    ]
    return [ContentItem(**it) for it in raw]


def get_catalog(force_reload: bool = False) -> List[ContentItem]:
    global _CATALOG_CACHE
    if (not force_reload) and _CATALOG_CACHE is not None:
        return _CATALOG_CACHE
    path = (getattr(config, "CONTENT_CATALOG_PATH", None) or "").strip()
    if path:
        if not os.path.exists(path):
            # Fall back to default sample silently
            _CATALOG_CACHE = _default_sample()
            return _CATALOG_CACHE
        try:
            _CATALOG_CACHE = _load_from_path(path)
            return _CATALOG_CACHE
        except Exception:
            # Fall back to default sample if parsing fails
            _CATALOG_CACHE = _default_sample()
            return _CATALOG_CACHE
    # No path provided: use default sample
    _CATALOG_CACHE = _default_sample()
    return _CATALOG_CACHE


def search_content(
    *,
    topics: List[str],
    ability_theta: Optional[float] = None,
    top_k: int = 3,
) -> ContentSearchResult:
    items = get_catalog()
    if not items:
        return ContentSearchResult(items=[])

    # Normalize topics to lowercase for matching
    tset = {t.strip().lower() for t in topics if t and isinstance(t, str)}
    if not tset:
        tset = set()

    # Map ability to a coarse difficulty target
    # theta ~ N(0,1), map to {2,3,4} on a 1..5 scale
    target_diff = 3.0
    if isinstance(ability_theta, (int, float)):
        if ability_theta < -0.5:
            target_diff = 2.0
        elif ability_theta > 0.5:
            target_diff = 4.0

    def score_item(ci: ContentItem) -> float:
        # Topic overlap
        tags = {x.strip().lower() for x in (ci.topic_tags or [])}
        overlap = len(tags & tset)
        # Difficulty proximity (smaller distance is better)
        if ci.difficulty is None:
            diff_score = 0.5
        else:
            dist = abs(float(ci.difficulty) - float(target_diff))
            diff_score = max(0.0, 1.0 - (dist / 3.0))  # crude normalization
        # Popularity
        pop = float(ci.popularity_score or 0.0)
        # Weighted sum
        return 2.0 * overlap + 1.0 * diff_score + 0.5 * pop

    ranked = sorted(items, key=score_item, reverse=True)
    out: List[ContentItem] = []
    for ci in ranked:
        # Only include if there is at least some topical relevance when topics provided
        if tset:
            if not set(ci.topic_tags or []) & tset:
                continue
        out.append(ci)
        if len(out) >= max(1, int(top_k)):
            break
    return ContentSearchResult(items=out)
