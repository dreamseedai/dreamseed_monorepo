"""
LLM 라우팅 공통 타입 및 상수
============================
"""

from __future__ import annotations
from typing import Literal

# 지원 언어 화이트리스트
SUPPORTED_LANGS = ["ko", "en", "zh-Hans", "zh-Hant"]
DEFAULT_LANG = "ko"

# 언어 타입
LangCode = Literal["ko", "en", "zh-Hans", "zh-Hant"]


# 프로바이더 타입
class Provider:
    """LLM 프로바이더 상수"""

    LOCAL_KO = "local_ko"
    LOCAL_EN = "local_en"
    DEEPSEEK = "deepseek"


ProviderType = Literal["local_ko", "local_en", "deepseek"]
