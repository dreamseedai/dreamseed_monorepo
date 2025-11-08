"""AI Empathy Engine - Rule-based encouragement message generator

Generates personalized, emotive messages for students based on:
- Learning progress (theta_delta from IRT)
- Mood history
- Study patterns

This is a simple rule-based system. Replace with LLM later for more nuanced messaging.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Literal

MoodType = Literal['happy', 'neutral', 'sad']
ToneType = Literal['warm', 'gentle', 'energetic']


# Message templates (Korean, emotive)
TEMPLATES = {
    'strong_up': "이번 주 {delta:+.2f}만큼 성장했어요! 꾸준함이 빛나요 ✨",
    'moderate_up': "조금씩 올라가고 있어요. 이 페이스면 충분해요 🌱",
    'steady': "꾸준한 리듬이 좋아요. 오늘도 20분만 집중해볼까요? 💪",
    'slight_down': "괜찮아요. 오늘은 가벼운 문제부터 다시 시작해봐요. 함께 천천히 가요 🌱",
    'strong_down': "힘들었죠? 잠깐 쉬었다가 다시 시작해요. 당신은 잘 하고 있어요 💖",
}

# Mood-specific additions
MOOD_ADDITIONS = {
    'sad': " 힘들었죠? 잠깐 산책하고 다시 시작해요. 당신은 잘 하고 있어요 💖",
    'happy': " 좋은 에너지가 느껴져요! 오늘도 파이팅 🎉",
    'neutral': "",
}


@dataclass
class Message:
    """Generated AI message with tone metadata"""
    text: str
    tone: ToneType
    context: dict  # Metadata for debugging/analysis


def make_message(
    theta_delta_7d: float,
    mood: MoodType | None = None,
    streak_days: int = 0
) -> Message:
    """Generate encouraging message based on recent performance and mood
    
    Args:
        theta_delta_7d: 7-day average theta change (IRT ability)
        mood: Current mood ('happy' | 'neutral' | 'sad')
        streak_days: Consecutive days of learning activity
        
    Returns:
        Message object with text, tone, and context
        
    Examples:
        >>> msg = make_message(theta_delta_7d=0.08, mood='happy')
        >>> msg.text
        '이번 주 +0.08만큼 성장했어요! 꾸준함이 빛나요 ✨ 좋은 에너지가 느껴져요! 오늘도 파이팅 🎉'
        >>> msg.tone
        'energetic'
    """
    tone: ToneType = 'warm'
    
    # Select base message based on theta delta
    if theta_delta_7d > 0.05:
        # Strong positive growth
        base_msg = TEMPLATES['strong_up'].format(delta=theta_delta_7d)
        tone = 'energetic'
    elif theta_delta_7d > 0.02:
        # Moderate positive growth
        base_msg = TEMPLATES['moderate_up']
        tone = 'warm'
    elif theta_delta_7d > -0.02:
        # Steady (no significant change)
        base_msg = TEMPLATES['steady']
        tone = 'warm'
    elif theta_delta_7d > -0.05:
        # Slight decline
        base_msg = TEMPLATES['slight_down']
        tone = 'gentle'
    else:
        # Strong decline
        base_msg = TEMPLATES['strong_down']
        tone = 'gentle'
    
    # Add mood-specific encouragement
    mood_addition = MOOD_ADDITIONS.get(mood or 'neutral', '')
    
    # Override tone if mood is sad (always gentle)
    if mood == 'sad':
        tone = 'gentle'
    elif mood == 'happy' and tone == 'warm':
        tone = 'energetic'
    
    # Add streak bonus message
    streak_msg = ""
    if streak_days >= 7:
        streak_msg = f" 🔥 {streak_days}일 연속 학습! 대단해요!"
    elif streak_days >= 3:
        streak_msg = f" 💪 {streak_days}일 연속! 이 리듬 좋아요."
    
    final_text = base_msg + mood_addition + streak_msg
    
    return Message(
        text=final_text,
        tone=tone,
        context={
            'theta_delta_7d': theta_delta_7d,
            'mood': mood,
            'streak_days': streak_days,
            'template_used': _get_template_name(theta_delta_7d)
        }
    )


def _get_template_name(theta_delta: float) -> str:
    """Helper: Get template name for context"""
    if theta_delta > 0.05:
        return 'strong_up'
    elif theta_delta > 0.02:
        return 'moderate_up'
    elif theta_delta > -0.02:
        return 'steady'
    elif theta_delta > -0.05:
        return 'slight_down'
    else:
        return 'strong_down'


# Quick function for backward compatibility
def generate_message(theta_delta_7d: float, mood: MoodType | None) -> tuple[str, str]:
    """Legacy interface: returns (message, tone) tuple
    
    Deprecated: Use make_message() instead for full context
    """
    msg = make_message(theta_delta_7d, mood)
    return msg.text, msg.tone
