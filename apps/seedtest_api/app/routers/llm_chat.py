"""
LLM 채팅 라우터
===============
Accept-Language 기반 자동 언어 감지 및 모델 라우팅.
"""

from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
import logging

from shared.llm.smart_router import dispatch_by_lang
from shared.llm.providers import call_deepseek, call_local_en, call_local_ko
from shared.llm.types import Provider
from shared.llm.middleware import get_request_language

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1", tags=["LLM Chat"])


class ChatRequest(BaseModel):
    """채팅 요청"""

    messages: list[Dict[str, str]]
    model: str = "auto"
    max_tokens: int = 200
    temperature: float = 0.7


class ChatResponse(BaseModel):
    """채팅 응답"""

    choices: list[Dict[str, Any]]
    detected_language: str
    model_type: str  # 'local' or 'cloud'


@router.post("/chat", response_model=ChatResponse)
async def chat(request: Request, body: ChatRequest):
    """
    자동 언어 감지 채팅 엔드포인트.

    Headers:
        - Accept-Language: 브라우저 언어 설정
        - X-Lang: 강제 언어 지정 (ko, en, zh-Hans, zh-Hant)

    Query:
        - ?lang=ko: 강제 언어 지정

    Body:
        - messages: OpenAI 호환 메시지 배열
        - model: 모델명 (기본값: auto - 언어별 자동 선택)
        - max_tokens: 최대 토큰 수
        - temperature: 샘플링 온도

    Returns:
        OpenAI 호환 응답 + 감지된 언어 정보
    """
    # 언어 감지
    lang = get_request_language(request)

    logger.info(f"Chat request: lang={lang}, messages={len(body.messages)}")

    # OpenAI 호환 요청 바디 구성
    llm_body = {
        "messages": body.messages,
        "max_tokens": body.max_tokens,
        "temperature": body.temperature,
    }

    # 프로바이더 맵
    providers = {
        Provider.DEEPSEEK: call_deepseek,
        Provider.LOCAL_EN: call_local_en,
        Provider.LOCAL_KO: call_local_ko,
    }

    try:
        # 언어별 자동 라우팅
        response = await dispatch_by_lang(lang, llm_body, providers)

        # 응답에 메타데이터 추가
        return ChatResponse(
            choices=response.get("choices", []),
            detected_language=lang,
            model_type="cloud" if lang.startswith("zh-") else "local",
        )

    except Exception as e:
        logger.error(f"LLM API error: {e}")

        # 장애 폴백: DeepSeek 실패 시 로컬 EN으로 우회
        if lang.startswith("zh-"):
            logger.warning(f"DeepSeek failed for {lang}, falling back to local EN")
            try:
                response = await providers[Provider.LOCAL_EN](llm_body)
                return ChatResponse(
                    choices=response.get("choices", []),
                    detected_language=lang,
                    model_type="local_fallback",
                )
            except Exception as fallback_error:
                logger.error(f"Fallback also failed: {fallback_error}")
                raise HTTPException(
                    status_code=500,
                    detail=f"LLM API error: {str(e)}, fallback failed: {str(fallback_error)}",
                )

        raise HTTPException(status_code=500, detail=f"LLM API error: {str(e)}")


@router.get("/language")
async def get_language(request: Request):
    """
    현재 감지된 언어 확인.

    Returns:
        감지된 언어 및 메타데이터
    """
    lang = get_request_language(request)

    return {
        "detected_language": lang,
        "accept_language": request.headers.get("accept-language"),
        "x_lang": request.headers.get("x-lang"),
        "query_lang": request.query_params.get("lang"),
        "model_type": "cloud" if lang.startswith("zh-") else "local",
    }
