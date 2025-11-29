"""
Locale and Language Detection
==============================
Parse Accept-Language header with q-value support.

Usage:
    from shared.web.locale import pick_accept_language

    lang = pick_accept_language('zh-CN,zh;q=0.9,en;q=0.8')
    # Returns: 'zh'
"""

from __future__ import annotations
from typing import Optional


def pick_accept_language(accept_language: Optional[str]) -> str:
    """
    Parse Accept-Language header and return best match.

    Supports q-value weighting and returns the highest priority language
    that matches our supported languages (ko, zh, en).

    Args:
        accept_language: Accept-Language header value
            Examples:
            - 'ko-KR,ko;q=0.9,en;q=0.8'
            - 'zh-CN,zh;q=0.9,en;q=0.8'
            - 'en-US,en;q=0.9'

    Returns:
        Language code ('ko', 'zh', 'en')
        Defaults to 'en' if no match or invalid header

    Examples:
        >>> pick_accept_language('zh-CN,zh;q=0.9,en;q=0.8')
        'zh'

        >>> pick_accept_language('ko-KR,ko;q=0.9,en;q=0.8')
        'ko'

        >>> pick_accept_language('en-US,en;q=0.9')
        'en'

        >>> pick_accept_language('fr-FR,fr;q=0.9')
        'en'  # Fallback to default

        >>> pick_accept_language(None)
        'en'  # Fallback to default

    Algorithm:
        1. Parse header into (language, q-value) pairs
        2. Sort by q-value (highest first)
        3. Return first match in supported languages (ko, zh, en)
        4. Default to 'en' if no match
    """
    if not accept_language:
        return "en"

    # Supported languages
    supported = {"ko", "zh", "en"}

    # Parse Accept-Language header
    languages = []
    for item in accept_language.split(","):
        item = item.strip()
        if not item:
            continue

        # Split language and q-value
        parts = item.split(";")
        lang_code = parts[0].strip().lower()

        # Extract q-value (default 1.0)
        q_value = 1.0
        if len(parts) > 1:
            for part in parts[1:]:
                part = part.strip()
                if part.startswith("q="):
                    try:
                        q_value = float(part[2:])
                    except ValueError:
                        q_value = 1.0
                    break

        # Normalize language code (ko-KR → ko, zh-CN → zh)
        lang_base = lang_code.split("-")[0]

        languages.append((lang_base, q_value))

    # Sort by q-value (highest first)
    languages.sort(key=lambda x: x[1], reverse=True)

    # Find first supported language
    for lang, _ in languages:
        if lang in supported:
            return lang

    # Default to English
    return "en"


# Export main function
__all__ = ["pick_accept_language"]
