"""
Empathy Prompt Templates
=========================
Language-aware system and user prompts for student encouragement.

Supports:
- Korean (ko): 따뜻하고 공감하는 톤
- Chinese (zh): 温暖鼓励型
- English (en): Warm and encouraging

Usage:
    from shared.llm.prompts.empathy import build_system, build_user

    system = build_system('ko')
    user = build_user(theta_delta_7d=0.08, mood='happy', streak=5, goal_titles=['수학 3문제'])
"""

from __future__ import annotations


def build_system(lang: str) -> str:
    """
    Build system prompt based on language.

    Args:
        lang: Language code ('ko', 'zh', 'en', or variants like 'ko-KR')

    Returns:
        System prompt string

    Examples:
        >>> build_system('ko')
        '너는 학생의 감정을 공감하고 동기를 북돋우는 코치야...'

        >>> build_system('en')
        'You are a warm, encouraging study coach...'
    """
    if lang.startswith("ko"):
        return """너는 학생의 감정을 공감하고 동기를 북돋우는 코치야.
            - 말투는 따뜻하고 간결하게, 이모지 1~2개까지.
            - 구체적/실행 가능한 한 줄 행동 제안 포함.
            - 비난/압박 금지.
            - 한국어로 답해.
            """

    if lang.startswith("zh"):
        return """你是一个温暖、鼓励型学习教练。
            - 语气真诚简洁，可以使用1~2个表情符号。
            - 提供可执行的一句话建议。
            - 不要指责或施压。
            - 用中文回答。
            """

    # Default: English
    return """You are a warm, encouraging study coach.
        - Keep it concise and specific, up to 2 emojis.
        - Include one actionable suggestion.
        - Avoid blame or pressure.
        - Reply in English.
        """


def build_user(
    theta_delta_7d: float, mood: str | None, streak: int, goal_titles: list[str]
) -> str:
    """
    Build user prompt with student context.

    Args:
        theta_delta_7d: 7-day IRT theta change
        mood: Student's mood ('happy', 'neutral', 'sad', or None)
        streak: Consecutive study days
        goal_titles: List of goal titles

    Returns:
        User prompt string

    Examples:
        >>> build_user(0.08, 'happy', 5, ['수학 3문제', '영어 단어 20개'])
        'Context: 7-day growth delta=+0.08, mood=happy, streak_days=5, goals=수학 3문제, 영어 단어 20개.\\n...'
    """
    mood_txt = mood or "unknown"
    goals = ", ".join(goal_titles[:3]) if goal_titles else "no goals set"

    return (
        f"Context: 7-day growth delta={theta_delta_7d:+.2f}, mood={mood_txt}, "
        f"streak_days={streak}, goals={goals}.\n"
        "Write 1-2 short sentences of encouragement with a concrete next step."
    )
