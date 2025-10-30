from __future__ import annotations

from apps.seedtest_api.schemas.analysis import TopicInsight
from apps.seedtest_api.services.recommendation import ContentBasedRecommender


def _weak(topic: str, acc: float) -> TopicInsight:
    return TopicInsight(topic=topic, accuracy=acc, correct=1, total=4, strength=False)


def test_content_recommender_uses_ability_for_fallback_low():
    # Topic not in default catalog sample -> search yields no items -> fallback path
    insights = [_weak("미적분", 0.25)]
    rec = ContentBasedRecommender().recommend(
        insights, ability_theta=-0.3, top_k=1
    )
    assert rec and any("기초" in r.message for r in rec)


def test_content_recommender_uses_ability_for_fallback_high():
    insights = [_weak("미적분", 0.25)]
    rec = ContentBasedRecommender().recommend(
        insights, ability_theta=0.7, top_k=1
    )
    assert rec and any("핵심" in r.message for r in rec)
