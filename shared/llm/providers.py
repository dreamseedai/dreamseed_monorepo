"""
LLM 프로바이더 어댑터
====================
각 LLM 서비스(로컬/클라우드)에 대한 HTTP 클라이언트 어댑터.

환경 변수:
    DEEPSEEK_API_KEY: DeepSeek API 키
    LOCAL_KO_URL: 한국어 로컬 LLM URL (기본: http://127.0.0.1:9001/v1/chat/completions)
    LOCAL_EN_URL: 영어 로컬 LLM URL (기본: http://127.0.0.1:9002/v1/chat/completions)
"""
from __future__ import annotations
import os
import logging
from typing import Any, Dict, Optional

import httpx

from .types import Provider

logger = logging.getLogger(__name__)

# 환경 변수
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
LOCAL_KO_URL = os.getenv("LOCAL_KO_URL", "http://127.0.0.1:9001/v1/chat/completions")
LOCAL_EN_URL = os.getenv("LOCAL_EN_URL", "http://127.0.0.1:9002/v1/chat/completions")
DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"


async def post_json(
    url: str,
    json: Dict[str, Any],
    headers: Optional[Dict[str, str]] = None,
    timeout: float = 60.0
) -> Dict[str, Any]:
    """
    JSON POST 요청 헬퍼.
    
    Args:
        url: 요청 URL
        json: 요청 바디
        headers: HTTP 헤더
        timeout: 타임아웃 (초)
    
    Returns:
        응답 JSON
    
    Raises:
        httpx.HTTPError: HTTP 에러
    """
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(url, json=json, headers=headers or {})
        response.raise_for_status()
        return response.json()


async def call_deepseek(body: Dict[str, Any]) -> Dict[str, Any]:
    """
    DeepSeek API 호출.
    
    Args:
        body: OpenAI 호환 요청 바디
    
    Returns:
        응답 JSON
    
    Raises:
        AssertionError: API 키 미설정
        httpx.HTTPError: API 에러
    """
    if not DEEPSEEK_API_KEY:
        raise ValueError("DEEPSEEK_API_KEY environment variable is required")
    
    logger.info("Calling DeepSeek API")
    
    return await post_json(
        DEEPSEEK_URL,
        body,
        headers={"Authorization": f"Bearer {DEEPSEEK_API_KEY}"}
    )


async def call_local_ko(body: Dict[str, Any]) -> Dict[str, Any]:
    """
    로컬 한국어 LLM 호출.
    
    Args:
        body: OpenAI 호환 요청 바디
    
    Returns:
        응답 JSON
    """
    logger.info(f"Calling local Korean LLM at {LOCAL_KO_URL}")
    return await post_json(LOCAL_KO_URL, body)


async def call_local_en(body: Dict[str, Any]) -> Dict[str, Any]:
    """
    로컬 영어 LLM 호출.
    
    Args:
        body: OpenAI 호환 요청 바디
    
    Returns:
        응답 JSON
    """
    logger.info(f"Calling local English LLM at {LOCAL_EN_URL}")
    return await post_json(LOCAL_EN_URL, body)


# 프로바이더 맵
PROVIDER_MAP = {
    Provider.LOCAL_KO: call_local_ko,
    Provider.LOCAL_EN: call_local_en,
    Provider.DEEPSEEK: call_deepseek,
}


async def dispatch_by_provider(
    provider: str,
    body: Dict[str, Any]
) -> Dict[str, Any]:
    """
    프로바이더별 디스패치.
    
    Args:
        provider: 프로바이더 타입 (Provider.LOCAL_KO, LOCAL_EN, DEEPSEEK)
        body: 요청 바디
    
    Returns:
        응답 JSON
    
    Raises:
        ValueError: 지원하지 않는 프로바이더
    """
    if provider not in PROVIDER_MAP:
        raise ValueError(f"Unsupported provider: {provider}")
    
    return await PROVIDER_MAP[provider](body)
