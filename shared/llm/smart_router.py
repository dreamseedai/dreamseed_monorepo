"""
스마트 LLM 라우터
=================
언어별로 최적 모델/엔드포인트를 자동 선택하는 라우터.

라우팅 정책:
- ko, en → 로컬 LLM (RTX 5090)
- zh-Hans, zh-Hant → DeepSeek 클라우드

Features:
- 자동 모델 선택
- 폴백 메커니즘 (클라우드 장애 시 로컬로 폴백)
- 캐싱 지원 (선택)
- 에러 핸들링

Usage:
    from shared.llm.smart_router import smart_chat
    
    # 자동 라우팅
    response = await smart_chat(
        lang="zh-Hans",
        system="You are a helpful assistant",
        user="你好！"
    )
    
    # Request 객체에서 자동 감지
    from fastapi import Request
    response = await smart_chat_from_request(
        request=request,
        system="You are a helpful assistant",
        user="Hello!"
    )
"""
from __future__ import annotations
import logging
from typing import Optional
from fastapi import Request

from shared.config.llm import CFG
from .openai_compat import CLIENT_LOCAL, CLIENT_DEEPSEEK, LLMClient
from .lang_detect import is_chinese, clamp_supported
from .middleware import get_request_language
from .types import Provider
from .providers import dispatch_by_provider, PROVIDER_MAP


logger = logging.getLogger(__name__)


def choose_provider_by_lang(lang: str) -> str:
    """
    언어에 따라 프로바이더 선택.
    
    Args:
        lang: 언어 코드 (ko, en, zh-Hans, zh-Hant)
    
    Returns:
        프로바이더 타입 (Provider.LOCAL_KO, LOCAL_EN, DEEPSEEK)
    """
    lang = clamp_supported(lang)
    
    if lang.startswith("zh-"):
        return Provider.DEEPSEEK
    elif lang == "en":
        return Provider.LOCAL_EN
    else:
        return Provider.LOCAL_KO


async def dispatch_by_lang(
    lang: str,
    body: dict,
    providers: dict
) -> dict:
    """
    언어별 프로바이더 디스패치.
    
    Args:
        lang: 언어 코드
        body: 요청 바디
        providers: 프로바이더 맵 {Provider.XXX: callable}
    
    Returns:
        응답 JSON
    
    Example:
        >>> providers = {
        ...     Provider.LOCAL_KO: call_local_ko,
        ...     Provider.LOCAL_EN: call_local_en,
        ...     Provider.DEEPSEEK: call_deepseek,
        ... }
        >>> response = await dispatch_by_lang("ko", body, providers)
    """
    provider = choose_provider_by_lang(lang)
    
    if provider not in providers:
        raise ValueError(f"Provider {provider} not found in providers map")
    
    logger.info(f"Dispatching to {provider} for language {lang}")
    
    return await providers[provider](body)


class SmartRouter:
    """
    언어별 스마트 LLM 라우터.
    
    Attributes:
        local_client: 로컬 LLM 클라이언트 (RTX 5090)
        cloud_client: 클라우드 LLM 클라이언트 (DeepSeek)
        enable_fallback: 클라우드 장애 시 로컬 폴백 활성화
    """
    
    def __init__(
        self,
        local_client: Optional[LLMClient] = None,
        cloud_client: Optional[LLMClient] = None,
        enable_fallback: bool = True
    ):
        """
        스마트 라우터 초기화.
        
        Args:
            local_client: 로컬 클라이언트 (기본값: CLIENT_LOCAL)
            cloud_client: 클라우드 클라이언트 (기본값: CLIENT_DEEPSEEK)
            enable_fallback: 폴백 활성화 (기본값: True)
        """
        self.local_client = local_client or CLIENT_LOCAL
        self.cloud_client = cloud_client or CLIENT_DEEPSEEK
        self.enable_fallback = enable_fallback
    
    def choose_client(self, lang: str) -> tuple[LLMClient, str]:
        """
        언어에 따라 클라이언트와 모델 선택.
        
        Args:
            lang: 언어 코드 (ko, en, zh-Hans, zh-Hant)
        
        Returns:
            (클라이언트, 모델명) 튜플
        
        Routing:
            - ko → (local, Qwen2.5-7B-Instruct)
            - en → (local, Llama-3.1-8B-Instruct)
            - zh-Hans, zh-Hant → (cloud, deepseek-chat)
        """
        if is_chinese(lang):
            # 중국어 → DeepSeek 클라우드
            return self.cloud_client, CFG.model_zh
        elif lang == "en":
            # 영어 → 로컬 영어 모델
            return self.local_client, CFG.model_en
        else:
            # 한국어 (기본값) → 로컬 한국어 모델
            return self.local_client, CFG.model_ko
    
    async def chat(
        self,
        lang: str,
        system: str,
        user: str,
        max_tokens: Optional[int] = None,
        timeout: Optional[float] = None,
        temperature: float = 0.7
    ) -> str:
        """
        언어별 자동 라우팅 채팅.
        
        Args:
            lang: 언어 코드 (ko, en, zh-Hans, zh-Hant)
            system: 시스템 프롬프트
            user: 사용자 메시지
            max_tokens: 최대 토큰 수
            timeout: 타임아웃 (초)
            temperature: 샘플링 온도
        
        Returns:
            생성된 응답 텍스트
        
        Raises:
            httpx.HTTPError: API 에러
            httpx.TimeoutException: 타임아웃
        
        Example:
            >>> router = SmartRouter()
            >>> response = await router.chat(
            ...     lang="zh-Hans",
            ...     system="你是一个有帮助的助手",
            ...     user="你好！"
            ... )
        """
        client, model = self.choose_client(lang)
        
        logger.info(
            f"Routing to {'cloud' if is_chinese(lang) else 'local'} "
            f"(lang={lang}, model={model})"
        )
        
        try:
            response = await client.chat(
                model=model,
                system=system,
                user=user,
                max_tokens=max_tokens,
                timeout=timeout,
                temperature=temperature
            )
            return response
        
        except Exception as e:
            # 클라우드 장애 시 로컬로 폴백 (중국어만)
            if self.enable_fallback and is_chinese(lang):
                logger.warning(
                    f"Cloud API failed for {lang}, falling back to local: {e}"
                )
                try:
                    # 로컬 한국어 모델로 폴백 (간단 번역 라운드 트립 허용)
                    fallback_model = CFG.model_ko
                    logger.info(f"Fallback to local model: {fallback_model}")
                    
                    response = await self.local_client.chat(
                        model=fallback_model,
                        system=system,
                        user=user,
                        max_tokens=max_tokens,
                        timeout=timeout,
                        temperature=temperature
                    )
                    return response
                except Exception as fallback_error:
                    logger.error(f"Fallback also failed: {fallback_error}")
                    raise
            else:
                raise


# 전역 라우터 인스턴스
ROUTER = SmartRouter()


async def smart_chat(
    lang: str,
    system: str,
    user: str,
    max_tokens: Optional[int] = None,
    timeout: Optional[float] = None,
    temperature: float = 0.7
) -> str:
    """
    언어별 자동 라우팅 채팅 (전역 라우터 사용).
    
    Args:
        lang: 언어 코드 (ko, en, zh-Hans, zh-Hant)
        system: 시스템 프롬프트
        user: 사용자 메시지
        max_tokens: 최대 토큰 수
        timeout: 타임아웃 (초)
        temperature: 샘플링 온도
    
    Returns:
        생성된 응답 텍스트
    
    Example:
        >>> response = await smart_chat(
        ...     lang="ko",
        ...     system="당신은 도움이 되는 조수입니다",
        ...     user="안녕하세요!"
        ... )
    """
    return await ROUTER.chat(
        lang=lang,
        system=system,
        user=user,
        max_tokens=max_tokens,
        timeout=timeout,
        temperature=temperature
    )


async def smart_chat_from_request(
    request: Request,
    system: str,
    user: str,
    max_tokens: Optional[int] = None,
    timeout: Optional[float] = None,
    temperature: float = 0.7
) -> str:
    """
    Request 객체에서 언어를 자동 감지하여 채팅.
    
    Args:
        request: FastAPI Request 객체 (LangRouteMiddleware 필요)
        system: 시스템 프롬프트
        user: 사용자 메시지
        max_tokens: 최대 토큰 수
        timeout: 타임아웃 (초)
        temperature: 샘플링 온도
    
    Returns:
        생성된 응답 텍스트
    
    Example:
        >>> from fastapi import Request
        >>> 
        >>> @app.post("/chat")
        >>> async def chat(request: Request, message: str):
        ...     response = await smart_chat_from_request(
        ...         request=request,
        ...         system="You are a helpful assistant",
        ...         user=message
        ...     )
        ...     return {"response": response}
    """
    lang = get_request_language(request)
    return await smart_chat(
        lang=lang,
        system=system,
        user=user,
        max_tokens=max_tokens,
        timeout=timeout,
        temperature=temperature
    )
