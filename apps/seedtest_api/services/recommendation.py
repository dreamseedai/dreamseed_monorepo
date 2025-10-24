from __future__ import annotations

from typing import List, Optional

from ..schemas.analysis import RecommendationItem, TopicInsight


class BaseRecommender:
    name: str = "base"

    def recommend(
        self,
        insights: List[TopicInsight],
        *,
        ability_theta: Optional[float] = None,
        top_k: int = 3,
    ) -> List[RecommendationItem]:
        raise NotImplementedError


class RuleBasedRecommender(BaseRecommender):
    name = "rule"

    def recommend(
        self,
        insights: List[TopicInsight],
        *,
        ability_theta: Optional[float] = None,
        top_k: int = 3,
    ) -> List[RecommendationItem]:
        recs: List[RecommendationItem] = []
        weaknesses = [ti for ti in insights if ti.accuracy <= 0.6]
        for w in weaknesses[:top_k]:
            recs.append(
                RecommendationItem(
                    topic=w.topic,
                    kind="study",
                    message=f"{w.topic} 영역: 핵심 개념 복습과 유사 문항 반복 풀이를 권장합니다.",
                )
            )
        if not recs:
            recs.append(
                RecommendationItem(
                    kind="meta",
                    message="현재 전반적인 성취도가 양호합니다. 오답 노트 기반의 약점 보완과 시간 배분 연습을 지속하세요.",
                )
            )
        return recs


class ContentBasedRecommender(BaseRecommender):
    name = "content"

    def recommend(
        self,
        insights: List[TopicInsight],
        *,
        ability_theta: Optional[float] = None,
        top_k: int = 3,
    ) -> List[RecommendationItem]:
        # Use content catalog search to retrieve topic-matched resources ranked by difficulty proximity and popularity.
        try:
            from .content_catalog import search_content

            # Collect weakest topics by accuracy
            weaknesses = sorted(insights, key=lambda t: t.accuracy)[: max(1, top_k)]
            topics = [w.topic for w in weaknesses if w.topic]
            result = search_content(topics=topics, ability_theta=ability_theta, top_k=top_k)
            if result.items:
                out: List[RecommendationItem] = []
                for it in result.items:
                    url_part = f" ({it.url})" if it.url else ""
                    msg = f"{', '.join(it.topic_tags) or '학습'} 관련 추천: {it.title}{url_part}"
                    out.append(RecommendationItem(topic=topics[0] if topics else None, kind="content", message=msg))
                return out
        except Exception:
            # Fall back to simple phrasing if catalog unavailable
            pass

        # Fallback: craft slightly more specific messages for weakest topics.
        recs: List[RecommendationItem] = []
        weaknesses = sorted(insights, key=lambda t: t.accuracy)[:top_k]
        for w in weaknesses:
            level = "기초" if (ability_theta is not None and ability_theta < 0) else "핵심"
            recs.append(
                RecommendationItem(
                    topic=w.topic,
                    kind="study",
                    message=f"{w.topic} 영역: {level} 개념 강의와 유사 유형 문제 세트를 우선 추천합니다.",
                )
            )
        if not recs:
            recs.append(
                RecommendationItem(
                    kind="meta",
                    message="현재 전반적인 성취도가 양호합니다. 실전 모의와 시간을 기준으로 한 훈련을 권장합니다.",
                )
            )
        return recs


class HybridRecommender(BaseRecommender):
    name = "hybrid"

    def __init__(self) -> None:
        self.content = ContentBasedRecommender()
        self.rule = RuleBasedRecommender()

    def recommend(
        self,
        insights: List[TopicInsight],
        *,
        ability_theta: Optional[float] = None,
        top_k: int = 3,
    ) -> List[RecommendationItem]:
        # Try content-based; if it yields nothing, fall back to rule.
        recs = self.content.recommend(insights, ability_theta=ability_theta, top_k=top_k)
        if not recs:
            recs = self.rule.recommend(insights, ability_theta=ability_theta, top_k=top_k)
        return recs


def get_recommender(name: str) -> BaseRecommender:
    key = (name or "").strip().lower()
    if key == HybridRecommender.name:
        # Prefer the shared HybridRecommender when available, adapting to API RecommendationItem
        try:
            from shared.recommendation_engine import (
                ContentType,
                DifficultyLevel,
            )
            from shared.recommendation_engine import HybridRecommender as SharedHybrid
            from shared.recommendation_engine import (
                LearningContent,
            )
            from shared.recommendation_engine import StudentWeakness as SharedWeakness

            from .content_catalog import get_catalog

            class SharedHybridAdapter(BaseRecommender):
                name = "hybrid"

                def recommend(
                    self,
                    insights: List[TopicInsight],
                    *,
                    ability_theta: Optional[float] = None,
                    top_k: int = 3,
                ) -> List[RecommendationItem]:
                    # Build contents from catalog
                    items = get_catalog()
                    contents: list[LearningContent] = []
                    for it in items:
                        # Map simple format strings to ContentType enum best-effort
                        fmt = (it.format or "").lower()
                        ct = {
                            "video": ContentType.VIDEO,
                            "article": ContentType.ARTICLE,
                            "problems": ContentType.PRACTICE,
                            "practice": ContentType.PRACTICE,
                            "quiz": ContentType.QUIZ,
                            "concept": ContentType.CONCEPT,
                        }.get(fmt, ContentType.CONCEPT)
                        # Map difficulty to BEGINNER/INTERMEDIATE/ADVANCED heuristically
                        dl = DifficultyLevel.INTERMEDIATE
                        try:
                            if it.difficulty is not None:
                                d = float(it.difficulty)
                                if d <= 2.0:
                                    dl = DifficultyLevel.BEGINNER
                                elif d >= 4.0:
                                    dl = DifficultyLevel.ADVANCED
                                else:
                                    dl = DifficultyLevel.INTERMEDIATE
                        except Exception:
                            pass
                        contents.append(
                            LearningContent(
                                content_id=it.id,
                                title=it.title,
                                content_type=ct,
                                topics=list(it.topic_tags or []),
                                difficulty=dl,
                                description=", ".join(it.topic_tags or []),
                                url=it.url,
                                rating=it.popularity_score,
                            )
                        )
                    # Build weaknesses from insights
                    weaknesses: list[SharedWeakness] = []
                    for ti in insights:
                        imp = 1.0 - float(ti.accuracy)
                        weaknesses.append(
                            SharedWeakness(
                                topic=ti.topic,
                                accuracy=float(ti.accuracy),
                                n_attempts=0,
                                avg_difficulty=0.5,
                                importance=max(0.1, min(1.0, imp)),
                            )
                        )
                    hyb = SharedHybrid(contents, use_rules=True, use_content=True)
                    recs = hyb.recommend(
                        "api-user",
                        weaknesses,
                        student_ability=float(ability_theta) if isinstance(ability_theta, (int, float)) else 0.0,
                        top_k=int(top_k or 3),
                    )
                    # Convert to API RecommendationItem
                    out: list[RecommendationItem] = []
                    for r in recs:
                        url_part = f" ({r.content.url})" if r.content.url else ""
                        msg = f"{r.content.title} ({r.content.content_type.value}) - {r.reason}{url_part}"
                        out.append(RecommendationItem(topic=(r.match_topics[0] if r.match_topics else None), kind="content", message=msg))
                    if not out:
                        # fallback to rule phrasing
                        return RuleBasedRecommender().recommend(insights, ability_theta=ability_theta, top_k=top_k)
                    return out

            return SharedHybridAdapter()
        except Exception:
            # Fallback to internal hybrid
            return HybridRecommender()
    if key == ContentBasedRecommender.name:
        return ContentBasedRecommender()
    return RuleBasedRecommender()
