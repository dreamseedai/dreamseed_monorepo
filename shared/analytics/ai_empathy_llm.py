"""
LLM-based Empathy Engine
=========================
AI encouragement message generation using local LLM with fallback to rule-based.

Features:
- Language-aware model routing (KR → Qwen, ZH → Qwen, EN → Llama)
- Async LLM calls with timeout
- Graceful fallback to rule-based on error
- Tone detection based on mood and growth

Usage:
    from shared.analytics.ai_empathy_llm import make_message_llm
    
    msg, tone = await make_message_llm(
        theta_delta_7d=0.08,
        mood='happy',
        streak_days=5,
        goal_titles=['수학 3문제', '영어 단어 20개'],
        lang='ko'
    )
"""
from __future__ import annotations
from typing import Tuple
from shared.llm.openai_compat import CLIENT_LOCAL, CLIENT_DEEPSEEK, LLMClient
from shared.llm.prompts.empathy import build_system, build_user
from shared.config.llm import CFG
from shared.analytics.ai_empathy import make_message as fallback_rule


# Language to model mapping
LANG_TO_MODEL = {
    'ko': CFG.model_ko,
    'zh': CFG.model_zh,
    'en': CFG.model_en,
}


def pick_model_and_client(lang: str) -> Tuple[str, 'LLMClient']:
    """
    Select appropriate model and client based on language.
    
    Hybrid routing:
    - Korean (ko) → Local RTX 5090 (Qwen2.5-7B-Instruct)
    - English (en) → Local RTX 5090 (Llama-3.1-8B-Instruct)
    - Chinese (zh) → DeepSeek Cloud (deepseek-chat)
    
    Args:
        lang: Language code ('ko', 'zh', 'en', or variants)
    
    Returns:
        Tuple of (model_name, client_instance)
    
    Examples:
        >>> model, client = pick_model_and_client('ko-KR')
        >>> model
        'Qwen2.5-7B-Instruct'
        >>> client is CLIENT_LOCAL
        True
        
        >>> model, client = pick_model_and_client('zh-CN')
        >>> model
        'deepseek-chat'
        >>> client is CLIENT_DEEPSEEK
        True
    """
    # Determine language key
    key = 'en'
    if lang.startswith('ko'):
        key = 'ko'
    elif lang.startswith('zh'):
        key = 'zh'
    
    # Get model
    model = LANG_TO_MODEL.get(key, CFG.model_en)
    
    # Select client: Chinese → DeepSeek, others → Local
    client = CLIENT_DEEPSEEK if key == 'zh' else CLIENT_LOCAL
    
    return model, client


def pick_model(lang: str) -> str:
    """
    Select appropriate model based on language (backward compatibility).
    
    Args:
        lang: Language code ('ko', 'zh', 'en', or variants)
    
    Returns:
        Model name from config
    
    Examples:
        >>> pick_model('ko-KR')
        'Qwen2.5-7B-Instruct'
        
        >>> pick_model('en')
        'Llama-3.1-8B-Instruct'
    """
    model, _ = pick_model_and_client(lang)
    return model


async def make_message_llm(
    theta_delta_7d: float,
    mood: str | None,
    streak_days: int,
    goal_titles: list[str],
    lang: str = 'en'
) -> Tuple[str, str]:
    """
    Generate encouragement message using LLM with fallback.
    
    Args:
        theta_delta_7d: 7-day IRT theta change
        mood: Student's mood ('happy', 'neutral', 'sad', or None)
        streak_days: Consecutive study days
        goal_titles: List of goal titles
        lang: Language code ('ko', 'zh', 'en')
    
    Returns:
        Tuple of (message, tone)
        - message: Encouragement message
        - tone: 'warm', 'gentle', or 'energetic'
    
    Examples:
        >>> msg, tone = await make_message_llm(0.08, 'happy', 5, ['수학 3문제'], 'ko')
        >>> print(msg)
        '이번 주 정말 잘했어요! 수학 3문제 목표도 달성해봐요 ✨'
        >>> print(tone)
        'warm'
    
    Note:
        On LLM error or timeout, falls back to rule-based message generation.
    """
    try:
        # Select model and client based on language (hybrid routing)
        model, client = pick_model_and_client(lang)
        
        # Build prompts
        sys = build_system(lang)
        usr = build_user(theta_delta_7d, mood, streak_days, goal_titles)
        
        # Call LLM (local or cloud)
        text = await client.chat(model=model, system=sys, user=usr)
        
        # Determine tone based on context
        tone = 'gentle' if (mood == 'sad' or theta_delta_7d < -0.02) else 'warm'
        
        return text, tone
        
    except Exception:
        # Log error (optional)
        # logger.warning(f"LLM call failed: {e}, falling back to rule-based")
        
        # Fallback to rule-based message
        msg, tone = fallback_rule(theta_delta_7d, mood)
        return msg, tone


# Export main function
__all__ = ['make_message_llm', 'pick_model']
