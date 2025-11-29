# backend/services/emotion.py

from typing import Dict, List

# 감정별 기본 색상 코드 (UI용)
emotion_colors: Dict[str, str] = {
    "설렘": "#FFD700",  # 금색
    "슬픔": "#6495ED",  # 연파랑
    "분노": "#FF6347",  # 토마토 레드
    "행복": "#32CD32",  # 라임그린
    "피로": "#A9A9A9",  # 다크그레이
    "놀람": "#FF69B4",  # 핫핑크
    "불안": "#708090",  # 슬레이트 그레이
}

# 감정 유사군 (추천, 필터링 등에 활용)
emotion_clusters: Dict[str, List[str]] = {
    "설렘": ["설렘", "두근거림", "긴장"],
    "슬픔": ["슬픔", "그리움", "눈물"],
    "행복": ["행복", "즐거움", "만족감"],
    "분노": ["분노", "짜증", "폭발"],
    "피로": ["피곤함", "무기력", "지침"],
}


# 감정 이름 정규화 함수 (소문자 통일 등)
def normalize_emotion_name(raw: str) -> str:
    return raw.strip().replace(" ", "").lower()


def detect_emotion_from_text(text: str) -> str:
    text = text.lower()
    if "설렘" in text or "두근" in text:
        return "설렘"
    if "슬픔" in text or "눈물" in text:
        return "슬픔"
    if "행복" in text or "기쁨" in text:
        return "행복"
    if "분노" in text or "짜증" in text:
        return "분노"
    if "피로" in text or "지침" in text:
        return "피로"
    if "불안" in text or "걱정" in text:
        return "불안"
    if "놀람" in text or "깜짝" in text:
        return "놀람"
    return "기타"
