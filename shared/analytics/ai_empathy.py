"""
AI Empathy Engine
=================
Rule-based AI message generator for student encouragement.

This is a placeholder implementation using template-based rules.
Replace with LLM integration (OpenAI, Claude, etc.) for production.

Usage:
    msg, tone = make_message(theta_delta_7d=0.08, mood='happy')
    # Returns: ("이번 주 +0.08만큼 성장했어요! 꾸준함이 빛나요 ✨", "warm")
"""

from __future__ import annotations
from typing import Optional


# Message templates by growth pattern
TEMPLATES = {
    "up": "이번 주 {delta:+.2f}만큼 성장했어요! 꾸준함이 빛나요 ✨",
    "down": "괜찮아요. 오늘은 가벼운 문제부터 다시 시작해봐요. 함께 천천히 가요 🌱",
    "steady": "꾸준한 리듬이 좋아요. 오늘도 20분만 집중해볼까요? 💪",
}

# Mood-based additional messages
MOOD_MESSAGES = {
    "sad": " 힘들었죠? 잠깐 산책하고 다시 시작해요. 당신은 잘 하고 있어요 💖",
    "happy": " 좋은 기분이 느껴져요! 이 에너지로 한 걸음 더 나아가봐요 🌟",
    "neutral": " 오늘도 차근차근 해나가면 돼요. 작은 진전도 큰 의미가 있어요 🌿",
}


def make_message(theta_delta_7d: float, mood: Optional[str] = None) -> tuple[str, str]:
    """
    Generate AI encouragement message based on growth and mood.

    Args:
        theta_delta_7d: 7-day theta change (IRT ability parameter)
        mood: Student's mood ('happy', 'neutral', 'sad', or None)

    Returns:
        Tuple of (message, tone)
        - message: Encouragement message in Korean
        - tone: Message tone ('warm', 'gentle', 'energetic')

    Examples:
        >>> make_message(0.08, 'happy')
        ('이번 주 +0.08만큼 성장했어요! 꾸준함이 빛나요 ✨ 좋은 기분이 느껴져요!...', 'warm')

        >>> make_message(-0.05, 'sad')
        ('괜찮아요. 오늘은 가벼운 문제부터 다시 시작해봐요...', 'gentle')
    """
    tone = "warm"

    # Select base message by growth pattern
    if theta_delta_7d > 0.05:
        # Significant positive growth
        msg = TEMPLATES["up"].format(delta=theta_delta_7d)
        tone = "energetic"
    elif theta_delta_7d < -0.02:
        # Negative growth - need gentle encouragement
        msg = TEMPLATES["down"]
        tone = "gentle"
    else:
        # Steady progress
        msg = TEMPLATES["steady"]

    # Add mood-based message
    if mood in MOOD_MESSAGES:
        msg += MOOD_MESSAGES[mood]
        # Override tone if mood is sad
        if mood == "sad":
            tone = "gentle"
        elif mood == "happy":
            tone = "energetic"

    return msg, tone


def make_message_llm(
    theta_delta_7d: float,
    mood: Optional[str] = None,
    study_minutes: int = 0,
    tasks_done: int = 0,
    streak_days: int = 0,
) -> tuple[str, str]:
    """
    LLM-based message generation (placeholder).

    TODO: Implement with OpenAI/Claude API

    Args:
        theta_delta_7d: 7-day theta change
        mood: Student's mood
        study_minutes: Study time in minutes
        tasks_done: Number of completed tasks
        streak_days: Consecutive study days

    Returns:
        Tuple of (message, tone)
    """
    # Placeholder: Use rule-based for now
    # In production, call LLM API with context:
    # prompt = f"""
    # Generate an encouraging message for a student with:
    # - Growth: {theta_delta_7d:+.2f}
    # - Mood: {mood}
    # - Study time: {study_minutes} minutes
    # - Tasks completed: {tasks_done}
    # - Streak: {streak_days} days
    #
    # Message should be warm, empathetic, and in Korean.
    # """
    # response = openai.ChatCompletion.create(...)

    return make_message(theta_delta_7d, mood)


# Export main function
__all__ = ["make_message", "make_message_llm"]
