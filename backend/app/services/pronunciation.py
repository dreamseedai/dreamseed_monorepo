# services/pronunciation.py

from difflib import SequenceMatcher


def compare_pronunciation(user_text: str, correct_text: str) -> dict:
    """
    두 문장을 비교해 유사도와 차이점을 반환
    """
    similarity = SequenceMatcher(None, user_text, correct_text).ratio()
    return {
        "similarity": round(similarity * 100, 2),  # 백분율
        "is_close": similarity > 0.75,
        "user_text": user_text,
        "expected": correct_text,
    }
