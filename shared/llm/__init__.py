# LLM client modules
"""
LLM 스마트 라우팅 시스템
========================
Accept-Language 기반 자동 언어 감지 및 최적 모델 라우팅.

Quick Start:
    from shared.llm import smart_chat, LangRouteMiddleware

    # FastAPI 앱에 미들웨어 추가
    app.add_middleware(LangRouteMiddleware)

    # 자동 라우팅 채팅
    response = await smart_chat(
        lang="ko",
        system="You are a helpful assistant",
        user="안녕하세요!"
    )
"""

# 타입 및 상수
from .types import (
    SUPPORTED_LANGS,
    DEFAULT_LANG,
    LangCode,
    Provider,
    ProviderType,
)

# 언어 감지
from .lang_detect import (
    detect_language,
    parse_accept_language,
    normalize_lang_code,
    detect_from_text,
    clamp_supported,
    is_chinese,
    is_local_model,
    is_cloud_model,
)

# 미들웨어
from .middleware import (
    LangRouteMiddleware,
    get_request_language,
)

# 스마트 라우터
from .smart_router import (
    SmartRouter,
    smart_chat,
    smart_chat_from_request,
    dispatch_by_lang,
    choose_provider_by_lang,
    ROUTER,
)

# OpenAI 호환 클라이언트
from .openai_compat import (
    LLMClient,
    CLIENT,
    CLIENT_LOCAL,
    CLIENT_DEEPSEEK,
)

__all__ = [
    # 타입 및 상수
    "SUPPORTED_LANGS",
    "DEFAULT_LANG",
    "LangCode",
    "Provider",
    "ProviderType",
    # 언어 감지
    "detect_language",
    "parse_accept_language",
    "normalize_lang_code",
    "detect_from_text",
    "clamp_supported",
    "is_chinese",
    "is_local_model",
    "is_cloud_model",
    # 미들웨어
    "LangRouteMiddleware",
    "get_request_language",
    # 스마트 라우터
    "SmartRouter",
    "smart_chat",
    "smart_chat_from_request",
    "dispatch_by_lang",
    "choose_provider_by_lang",
    "ROUTER",
    # 클라이언트
    "LLMClient",
    "CLIENT",
    "CLIENT_LOCAL",
    "CLIENT_DEEPSEEK",
]
