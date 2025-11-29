#!/usr/bin/env python3
"""
LLM 스마트 라우팅 샘플 FastAPI 앱
==================================
Accept-Language 기반 자동 언어 감지 및 모델 라우팅 데모.

Usage:
    # 개발 서버 실행
    python ops/scripts/example_smart_routing_app.py

    # 또는 uvicorn 사용
    uvicorn ops.scripts.example_smart_routing_app:app --reload --port 8000

Requirements:
    - 로컬 LLM 서버 실행 (http://127.0.0.1:8001/v1)
    - DeepSeek API 키 설정 (환경변수 LLM_API_KEY_DEEPSEEK)
"""
import sys
import os

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from shared.llm.middleware import LangRouteMiddleware, get_request_language
from shared.llm.smart_router import smart_chat_from_request, smart_chat


# FastAPI 앱 생성
app = FastAPI(
    title="LLM 스마트 라우팅 데모",
    description="Accept-Language 기반 자동 언어 감지 및 모델 라우팅",
    version="1.0.0",
)

# 미들웨어 추가
app.add_middleware(LangRouteMiddleware)


# 요청 모델
class ChatRequest(BaseModel):
    message: str
    system: str = "You are a helpful assistant"
    max_tokens: int = 200
    temperature: float = 0.7


# 응답 모델
class ChatResponse(BaseModel):
    response: str
    detected_language: str
    model_type: str  # 'local' or 'cloud'


@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "message": "LLM 스마트 라우팅 API",
        "endpoints": {
            "/chat": "POST - 자동 언어 감지 채팅",
            "/chat/{lang}": "POST - 수동 언어 지정 채팅",
            "/language": "GET - 언어 감지만 테스트",
            "/docs": "GET - API 문서",
        },
    }


@app.get("/language")
async def detect_language_endpoint(request: Request):
    """
    언어 감지만 테스트하는 엔드포인트.

    Accept-Language 헤더를 기반으로 언어를 감지합니다.
    """
    lang = get_request_language(request)

    return {
        "detected_language": lang,
        "accept_language": request.headers.get("accept-language"),
        "forced_lang": request.query_params.get("lang")
        or request.headers.get("x-lang"),
        "model_type": "cloud" if lang.startswith("zh-") else "local",
    }


@app.post("/chat", response_model=ChatResponse)
async def chat_auto(request: Request, body: ChatRequest):
    """
    자동 언어 감지 채팅 엔드포인트.

    Accept-Language 헤더를 기반으로 언어를 자동 감지하고,
    적절한 모델로 라우팅합니다.

    - ko, en → 로컬 LLM (RTX 5090)
    - zh-Hans, zh-Hant → DeepSeek 클라우드
    """
    lang = get_request_language(request)

    try:
        response = await smart_chat_from_request(
            request=request,
            system=body.system,
            user=body.message,
            max_tokens=body.max_tokens,
            temperature=body.temperature,
        )

        return ChatResponse(
            response=response,
            detected_language=lang,
            model_type="cloud" if lang.startswith("zh-") else "local",
        )

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "error": str(e),
                "detected_language": lang,
                "message": "LLM API 호출 실패",
            },
        )


@app.post("/chat/{lang}", response_model=ChatResponse)
async def chat_manual(lang: str, body: ChatRequest):
    """
    수동 언어 지정 채팅 엔드포인트.

    URL 경로에서 언어를 직접 지정합니다.

    지원 언어:
    - ko: 한국어
    - en: 영어
    - zh-Hans: 중국어 간체
    - zh-Hant: 중국어 번체
    """
    # 언어 검증
    supported = {"ko", "en", "zh-Hans", "zh-Hant"}
    if lang not in supported:
        return JSONResponse(
            status_code=400,
            content={
                "error": f"지원하지 않는 언어: {lang}",
                "supported_languages": list(supported),
            },
        )

    try:
        response = await smart_chat(
            lang=lang,
            system=body.system,
            user=body.message,
            max_tokens=body.max_tokens,
            temperature=body.temperature,
        )

        return ChatResponse(
            response=response,
            detected_language=lang,
            model_type="cloud" if lang.startswith("zh-") else "local",
        )

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e), "language": lang, "message": "LLM API 호출 실패"},
        )


@app.get("/health")
async def health():
    """헬스 체크 엔드포인트"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    print("=" * 60)
    print("LLM 스마트 라우팅 샘플 앱 시작")
    print("=" * 60)
    print("URL: http://localhost:8000")
    print("Docs: http://localhost:8000/docs")
    print("=" * 60)

    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
