"""Recommendation Engine - 맞춤형 학습자료 추천

개인별 취약점 기반 학습 콘텐츠 추천 시스템
==========================================

이 모듈은 다음 기능을 제공합니다:
1. 규칙 기반 추천 (Rule-based)
2. 콘텐츠 기반 필터링 (Content-based Filtering)
3. 협업 필터링 (Collaborative Filtering)
4. 하이브리드 추천 (Hybrid)

References
----------
- Content-based Filtering: Pazzani & Billsus (2007)
- Collaborative Filtering: Koren et al. (2009)
- Hybrid Recommender Systems: Burke (2002)
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False


class ContentType(str, Enum):
    """학습 콘텐츠 유형"""
    VIDEO = "video"
    ARTICLE = "article"
    PRACTICE = "practice"
    QUIZ = "quiz"
    CONCEPT = "concept"


class DifficultyLevel(str, Enum):
    """난이도 레벨"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


@dataclass
class LearningContent:
    """학습 콘텐츠"""
    content_id: str
    title: str
    content_type: ContentType
    topics: List[str]
    difficulty: DifficultyLevel
    description: str
    url: Optional[str] = None
    duration_min: Optional[int] = None
    rating: Optional[float] = None
    
    # 메타데이터 (TF-IDF용)
    keywords: Optional[List[str]] = None
    
    def to_dict(self) -> dict:
        return {
            "content_id": self.content_id,
            "title": self.title,
            "content_type": self.content_type.value,
            "topics": self.topics,
            "difficulty": self.difficulty.value,
            "description": self.description,
            "url": self.url,
            "duration_min": self.duration_min,
            "rating": self.rating,
            "keywords": self.keywords,
        }


@dataclass
class StudentWeakness:
    """학생 취약점"""
    topic: str
    accuracy: float
    n_attempts: int
    avg_difficulty: float
    importance: float  # 중요도 (0~1)
    
    def to_dict(self) -> dict:
        return {
            "topic": self.topic,
            "accuracy": self.accuracy,
            "n_attempts": self.n_attempts,
            "avg_difficulty": self.avg_difficulty,
            "importance": self.importance,
        }


@dataclass
class Recommendation:
    """추천 결과"""
    content: LearningContent
    score: float
    reason: str
    match_topics: List[str]
    
    def to_dict(self) -> dict:
        return {
            "content": self.content.to_dict(),
            "score": self.score,
            "reason": self.reason,
            "match_topics": self.match_topics,
        }


# ==============================================================================
# Rule-based Recommender (Phase 1)
# ==============================================================================

class RuleBasedRecommender:
    """규칙 기반 추천 엔진
    
    학생의 취약 토픽에 대해 미리 정의된 규칙으로 콘텐츠를 추천합니다.
    """
    
    def __init__(self, contents: List[LearningContent]):
        self.contents = contents
        self._build_topic_index()
        
    def _build_topic_index(self):
        """토픽별 콘텐츠 인덱스 구축"""
        self.topic_index: Dict[str, List[LearningContent]] = {}
        for content in self.contents:
            for topic in content.topics:
                if topic not in self.topic_index:
                    self.topic_index[topic] = []
                self.topic_index[topic].append(content)
    
    def recommend(
        self,
        weaknesses: List[StudentWeakness],
        student_ability: float = 0.0,
        top_k: int = 5,
    ) -> List[Recommendation]:
        """규칙 기반 추천
        
        Parameters
        ----------
        weaknesses : List[StudentWeakness]
            학생의 취약점 목록
            
        student_ability : float
            학생 능력치 (θ)
            
        top_k : int
            추천 개수
            
        Returns
        -------
        List[Recommendation]
            추천 콘텐츠 목록
        """
        recommendations = []
        
        # 중요도 순으로 정렬
        sorted_weaknesses = sorted(
            weaknesses,
            key=lambda w: (w.importance, 1.0 - w.accuracy),
            reverse=True,
        )
        
        for weakness in sorted_weaknesses[:3]:  # 상위 3개 취약점
            # 해당 토픽의 콘텐츠 찾기
            candidates = self.topic_index.get(weakness.topic, [])
            
            for content in candidates:
                # 난이도 매칭
                difficulty_match = self._match_difficulty(
                    student_ability, weakness.accuracy, content.difficulty
                )
                
                if difficulty_match > 0.3:  # 최소 매칭 임계값
                    # 점수 계산
                    score = (
                        weakness.importance * 0.4 +
                        (1.0 - weakness.accuracy) * 0.3 +
                        difficulty_match * 0.3
                    )
                    
                    # 추천 이유 생성
                    reason = self._generate_reason(weakness, content)
                    
                    recommendations.append(Recommendation(
                        content=content,
                        score=score,
                        reason=reason,
                        match_topics=[weakness.topic],
                    ))
        
        # 점수 순으로 정렬
        recommendations.sort(key=lambda r: r.score, reverse=True)
        
        return recommendations[:top_k]
    
    def _match_difficulty(
        self,
        student_ability: float,
        topic_accuracy: float,
        content_difficulty: DifficultyLevel,
    ) -> float:
        """난이도 매칭 점수"""
        # 학생 레벨 판단
        if student_ability < -0.5 or topic_accuracy < 0.4:
            student_level = DifficultyLevel.BEGINNER
        elif student_ability > 0.5 and topic_accuracy > 0.7:
            student_level = DifficultyLevel.ADVANCED
        else:
            student_level = DifficultyLevel.INTERMEDIATE
        
        # 매칭 점수
        if student_level == content_difficulty:
            return 1.0
        elif abs(self._difficulty_to_num(student_level) - 
                 self._difficulty_to_num(content_difficulty)) == 1:
            return 0.5
        else:
            return 0.1
    
    def _difficulty_to_num(self, level: DifficultyLevel) -> int:
        mapping = {
            DifficultyLevel.BEGINNER: 1,
            DifficultyLevel.INTERMEDIATE: 2,
            DifficultyLevel.ADVANCED: 3,
        }
        return mapping[level]
    
    def _generate_reason(
        self,
        weakness: StudentWeakness,
        content: LearningContent,
    ) -> str:
        """추천 이유 생성"""
        if weakness.accuracy < 0.4:
            return f"'{weakness.topic}' 기본 개념 학습이 필요합니다 (정답률 {weakness.accuracy:.0%})"
        elif weakness.accuracy < 0.7:
            return f"'{weakness.topic}' 연습을 통해 실력을 향상시키세요 (정답률 {weakness.accuracy:.0%})"
        else:
            return f"'{weakness.topic}' 심화 학습으로 완성도를 높이세요"


# ==============================================================================
# Content-based Filtering (Phase 2)
# ==============================================================================

class ContentBasedRecommender:
    """콘텐츠 기반 필터링 추천 엔진
    
    TF-IDF를 사용하여 콘텐츠와 학생 취약점의 유사도를 계산합니다.
    """
    
    def __init__(self, contents: List[LearningContent]):
        self.contents = contents
        self._build_tfidf()
        
    def _build_tfidf(self):
        """TF-IDF 벡터 구축"""
        # 문서 집합: 각 콘텐츠의 키워드
        documents = []
        for content in self.contents:
            # 키워드가 없으면 토픽과 설명 사용
            if content.keywords:
                doc = content.keywords
            else:
                doc = content.topics + content.description.lower().split()
            documents.append(set(doc))
        
        # 전체 단어 집합
        all_words = set()
        for doc in documents:
            all_words.update(doc)
        
        self.vocabulary = list(all_words)
        self.word_to_idx = {word: idx for idx, word in enumerate(self.vocabulary)}
        
        # IDF 계산
        n_docs = len(documents)
        self.idf = {}
        for word in self.vocabulary:
            df = sum(1 for doc in documents if word in doc)
            self.idf[word] = math.log(n_docs / (df + 1))
        
        # 각 콘텐츠의 TF-IDF 벡터
        self.content_vectors = []
        for doc in documents:
            vector = [0.0] * len(self.vocabulary)
            # TF 계산 (단순 빈도)
            tf = {}
            for word in doc:
                tf[word] = tf.get(word, 0) + 1
            
            # TF-IDF
            for word, freq in tf.items():
                idx = self.word_to_idx[word]
                vector[idx] = freq * self.idf[word]
            
            self.content_vectors.append(vector)
    
    def recommend(
        self,
        weaknesses: List[StudentWeakness],
        student_ability: float = 0.0,
        top_k: int = 5,
    ) -> List[Recommendation]:
        """콘텐츠 기반 추천
        
        학생의 취약 토픽을 쿼리로 사용하여 유사한 콘텐츠를 찾습니다.
        """
        # 학생 취약점을 쿼리 벡터로 변환
        query_words = set()
        for weakness in weaknesses:
            query_words.add(weakness.topic.lower())
            # 중요도 가중치
            for _ in range(int(weakness.importance * 3)):
                query_words.add(weakness.topic.lower())
        
        # 쿼리 TF-IDF 벡터
        query_vector = [0.0] * len(self.vocabulary)
        for word in query_words:
            if word in self.word_to_idx:
                idx = self.word_to_idx[word]
                query_vector[idx] = self.idf.get(word, 0)
        
        # 코사인 유사도 계산
        similarities = []
        for i, content_vector in enumerate(self.content_vectors):
            sim = self._cosine_similarity(query_vector, content_vector)
            similarities.append((i, sim))
        
        # 유사도 순으로 정렬
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        # 추천 생성
        recommendations = []
        for i, sim in similarities[:top_k * 2]:  # 후보를 더 많이 뽑음
            content = self.contents[i]
            
            # 난이도 필터링
            if self._is_appropriate_difficulty(student_ability, content.difficulty):
                # 매칭된 토픽 찾기
                match_topics = [
                    w.topic for w in weaknesses
                    if w.topic.lower() in [t.lower() for t in content.topics]
                ]
                
                reason = f"'{', '.join(match_topics[:2])}' 학습에 적합한 콘텐츠입니다"
                
                recommendations.append(Recommendation(
                    content=content,
                    score=sim,
                    reason=reason,
                    match_topics=match_topics,
                ))
                
                if len(recommendations) >= top_k:
                    break
        
        return recommendations
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """코사인 유사도"""
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = math.sqrt(sum(a * a for a in vec1))
        norm2 = math.sqrt(sum(b * b for b in vec2))
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def _is_appropriate_difficulty(
        self,
        student_ability: float,
        content_difficulty: DifficultyLevel,
    ) -> bool:
        """적절한 난이도인지 확인"""
        if student_ability < -0.5:
            return content_difficulty in [DifficultyLevel.BEGINNER, DifficultyLevel.INTERMEDIATE]
        elif student_ability > 0.5:
            return content_difficulty in [DifficultyLevel.INTERMEDIATE, DifficultyLevel.ADVANCED]
        else:
            return True  # 중간 레벨은 모든 난이도 허용


# ==============================================================================
# Collaborative Filtering (Phase 3)
# ==============================================================================

class CollaborativeRecommender:
    """협업 필터링 추천 엔진
    
    유사한 학생들이 효과를 본 콘텐츠를 추천합니다.
    """
    
    def __init__(self):
        # 학생-콘텐츠 상호작용 데이터
        self.interaction_matrix: Dict[str, Dict[str, float]] = {}
        # 학생 프로필
        self.student_profiles: Dict[str, Dict] = {}
        
    def add_interaction(
        self,
        student_id: str,
        content_id: str,
        rating: float,
        improvement: Optional[float] = None,
    ):
        """상호작용 데이터 추가
        
        Parameters
        ----------
        student_id : str
        content_id : str
        rating : float
            평점 (0~1)
        improvement : float, optional
            학습 후 향상도
        """
        if student_id not in self.interaction_matrix:
            self.interaction_matrix[student_id] = {}
        
        # 평점과 향상도를 결합
        score = rating
        if improvement is not None:
            score = 0.5 * rating + 0.5 * improvement
        
        self.interaction_matrix[student_id][content_id] = score
    
    def add_student_profile(
        self,
        student_id: str,
        ability: float,
        weak_topics: List[str],
    ):
        """학생 프로필 추가"""
        self.student_profiles[student_id] = {
            "ability": ability,
            "weak_topics": set(weak_topics),
        }
    
    def recommend(
        self,
        student_id: str,
        weaknesses: List[StudentWeakness],
        top_k: int = 5,
    ) -> List[Tuple[str, float, str]]:
        """협업 필터링 추천
        
        Returns
        -------
        List[Tuple[str, float, str]]
            (content_id, score, reason)
        """
        if student_id not in self.student_profiles:
            return []
        
        # 유사한 학생 찾기
        similar_students = self._find_similar_students(student_id, top_k=10)
        
        # 유사 학생들이 좋아한 콘텐츠 집계
        content_scores: Dict[str, float] = {}
        content_counts: Dict[str, int] = {}
        
        for similar_id, similarity in similar_students:
            if similar_id in self.interaction_matrix:
                for content_id, score in self.interaction_matrix[similar_id].items():
                    # 이미 본 콘텐츠는 제외
                    if student_id in self.interaction_matrix and \
                       content_id in self.interaction_matrix[student_id]:
                        continue
                    
                    content_scores[content_id] = content_scores.get(content_id, 0.0) + score * similarity
                    content_counts[content_id] = content_counts.get(content_id, 0) + 1
        
        # 평균 점수 계산
        recommendations = []
        for content_id, total_score in content_scores.items():
            count = content_counts[content_id]
            avg_score = total_score / count
            
            reason = f"유사한 학생 {count}명이 이 콘텐츠로 학습 효과를 보았습니다"
            recommendations.append((content_id, avg_score, reason))
        
        # 점수 순으로 정렬
        recommendations.sort(key=lambda x: x[1], reverse=True)
        
        return recommendations[:top_k]
    
    def _find_similar_students(
        self,
        student_id: str,
        top_k: int = 10,
    ) -> List[Tuple[str, float]]:
        """유사한 학생 찾기"""
        if student_id not in self.student_profiles:
            return []
        
        target_profile = self.student_profiles[student_id]
        similarities = []
        
        for other_id, other_profile in self.student_profiles.items():
            if other_id == student_id:
                continue
            
            # 유사도 계산: 능력치 차이 + 취약 토픽 겹침
            ability_diff = abs(target_profile["ability"] - other_profile["ability"])
            ability_sim = 1.0 / (1.0 + ability_diff)
            
            # Jaccard 유사도 (취약 토픽)
            target_topics = target_profile["weak_topics"]
            other_topics = other_profile["weak_topics"]
            
            if len(target_topics) == 0 or len(other_topics) == 0:
                topic_sim = 0.0
            else:
                intersection = len(target_topics & other_topics)
                union = len(target_topics | other_topics)
                topic_sim = intersection / union if union > 0 else 0.0
            
            # 종합 유사도
            similarity = 0.4 * ability_sim + 0.6 * topic_sim
            
            similarities.append((other_id, similarity))
        
        # 유사도 순으로 정렬
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        return similarities[:top_k]


# ==============================================================================
# Hybrid Recommender (Phase 4)
# ==============================================================================

class HybridRecommender:
    """하이브리드 추천 엔진
    
    규칙 기반, 콘텐츠 기반, 협업 필터링을 결합합니다.
    """
    
    def __init__(
        self,
        contents: List[LearningContent],
        use_rules: bool = True,
        use_content: bool = True,
        use_collaborative: bool = False,
    ):
        self.use_rules = use_rules
        self.use_content = use_content
        self.use_collaborative = use_collaborative
        
        if use_rules:
            self.rule_recommender = RuleBasedRecommender(contents)
        
        if use_content:
            self.content_recommender = ContentBasedRecommender(contents)
        
        if use_collaborative:
            self.collab_recommender = CollaborativeRecommender()
        
        self.contents_map = {c.content_id: c for c in contents}
    
    def recommend(
        self,
        student_id: str,
        weaknesses: List[StudentWeakness],
        student_ability: float = 0.0,
        top_k: int = 5,
    ) -> List[Recommendation]:
        """하이브리드 추천"""
        all_recommendations: Dict[str, Recommendation] = {}
        
        # 1. 규칙 기반 추천
        if self.use_rules:
            rule_recs = self.rule_recommender.recommend(
                weaknesses, student_ability, top_k=top_k * 2
            )
            for rec in rule_recs:
                cid = rec.content.content_id
                if cid not in all_recommendations:
                    all_recommendations[cid] = rec
                    rec.score *= 0.4  # 가중치
        
        # 2. 콘텐츠 기반 추천
        if self.use_content:
            content_recs = self.content_recommender.recommend(
                weaknesses, student_ability, top_k=top_k * 2
            )
            for rec in content_recs:
                cid = rec.content.content_id
                if cid in all_recommendations:
                    all_recommendations[cid].score += rec.score * 0.4
                else:
                    all_recommendations[cid] = rec
                    rec.score *= 0.4
        
        # 3. 협업 필터링 추천
        if self.use_collaborative:
            collab_recs = self.collab_recommender.recommend(
                student_id, weaknesses, top_k=top_k * 2
            )
            for content_id, score, reason in collab_recs:
                if content_id in self.contents_map:
                    content = self.contents_map[content_id]
                    match_topics = [w.topic for w in weaknesses if w.topic in content.topics]
                    
                    if content_id in all_recommendations:
                        all_recommendations[content_id].score += score * 0.2
                    else:
                        all_recommendations[content_id] = Recommendation(
                            content=content,
                            score=score * 0.2,
                            reason=reason,
                            match_topics=match_topics,
                        )
        
        # 점수 순으로 정렬
        final_recs = sorted(
            all_recommendations.values(),
            key=lambda r: r.score,
            reverse=True,
        )
        
        return final_recs[:top_k]

    def recommend_text(
        self,
        student_id: str,
        weaknesses: List[StudentWeakness],
        student_ability: float = 0.0,
        top_k: int = 5,
    ) -> List[str]:
        """사람이 읽기 쉬운 한 줄 텍스트 추천 결과를 반환합니다.

        예) "확률의 기본 개념 (video) - '확률' 기본 개념 학습이 필요합니다 (정답률 30%)"
        """
        recs = self.recommend(student_id, weaknesses, student_ability=student_ability, top_k=top_k)
        lines: List[str] = []
        for r in recs:
            ctype = getattr(r.content.content_type, "value", str(r.content.content_type))
            title = r.content.title
            reason = r.reason
            lines.append(f"{title} ({ctype}) - {reason}")
        return lines


__all__ = [
    "LearningContent",
    "StudentWeakness",
    "Recommendation",
    "ContentType",
    "DifficultyLevel",
    "RuleBasedRecommender",
    "ContentBasedRecommender",
    "CollaborativeRecommender",
    "HybridRecommender",
]

