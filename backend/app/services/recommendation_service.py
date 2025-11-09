# backend/services/recommendation_service.py

import re
from typing import List, Dict

from app.services.emotion import emotion_clusters, normalize_emotion_name
from app.services.openai_service import ask_gpt
from data.emotion_tags import content_items  # 실제로는 DB 또는 JSON 불러오기


def recommend_by_emotion(emotion: str) -> List[Dict]:
    """
    감정을 기반으로 관련 클러스터를 가져와 콘텐츠를 추천
    """
    normalized = normalize_emotion_name(emotion)
    cluster = emotion_clusters.get(normalized, [normalized])

    recommended = [
        item
        for item in content_items
        if any(tag in cluster for tag in item["emotion_tags"])
    ]

    return recommended


def build_gpt_prompt(emotion: str) -> str:
    """
    감정 클러스터 기반 GPT 추천 프롬프트 생성
    """
    normalized = normalize_emotion_name(emotion)
    cluster = emotion_clusters.get(normalized, [normalized])
    keywords = ", ".join(cluster)

    prompt = f"""
당신은 감정 기반 콘텐츠 큐레이터입니다.
사용자의 현재 감정은 '{emotion}'이며, 관련 감정 키워드는 [{keywords}] 입니다.
K-pop, K-drama, 음식, 영상, 블로그 등 다양한 콘텐츠를 3~5개 추천해 주세요.

각 항목은 다음 형식을 따르세요:
제목 - 설명 (출처 URL)

예시:
도깨비 고백 장면 - 설렘 가득한 드라마 명장면 (https://example.com/goblin)
"""
    return prompt.strip()


def gpt_emotion_recommend(emotion: str) -> List[Dict]:
    """
    GPT에게 감정 기반 콘텐츠 추천을 요청하고, 구조화된 리스트로 반환
    """
    prompt = build_gpt_prompt(emotion)
    raw_response = ask_gpt(prompt)

    parsed: List[Dict] = []
    lines = raw_response.strip().split("\n")

    for line in lines:
        # 형식: 제목 - 설명 (URL)
        match = re.match(r"^\d*\.*\s*(.+?)\s*-\s*(.+?)\s*\((http.+?)\)", line.strip())
        if match:
            title, description, url = match.groups()
            parsed.append(
                {
                    "title": title.strip(),
                    "description": description.strip(),
                    "url": url.strip(),
                    "source": "GPT",
                }
            )

    return parsed
