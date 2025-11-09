"""
언어 라우팅 미들웨어
====================
FastAPI 미들웨어로 요청별 언어를 자동 감지하고 request.state에 저장.

Features:
- Accept-Language 헤더 자동 파싱
- 강제 언어 지정 지원 (?lang= 또는 X-Lang 헤더)
- 쿠키/JWT 기반 언어 선호 지원
- 응답 헤더에 감지된 언어 추가 (X-Resolved-Lang)

Usage:
    from fastapi import FastAPI
    from shared.llm.middleware import LangRouteMiddleware
    
    app = FastAPI()
    app.add_middleware(LangRouteMiddleware)
    
    @app.get("/test")
    async def test(request: Request):
        lang = request.state.route_lang  # 'ko', 'en', 'zh-Hans', 'zh-Hant'
        return {"language": lang}

Environment Variables:
    DEFAULT_LANG: 기본 언어 (기본값: ko)
"""
from __future__ import annotations
import os
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from .lang_detect import detect_language, SUPPORTED_LANGS


class LangRouteMiddleware(BaseHTTPMiddleware):
    """
    언어 라우팅 미들웨어.
    
    요청마다 언어를 자동 감지하고 request.state.route_lang에 저장.
    응답 헤더에 X-Resolved-Lang을 추가하여 감지된 언어를 반환.
    
    Attributes:
        default_lang: 기본 언어 (환경변수 DEFAULT_LANG 또는 'ko')
    """
    
    def __init__(self, app: ASGIApp, default_lang: str = "ko"):
        """
        미들웨어 초기화.
        
        Args:
            app: ASGI 애플리케이션
            default_lang: 기본 언어 (기본값: 'ko')
        """
        super().__init__(app)
        self.default_lang = os.getenv("DEFAULT_LANG", default_lang)
        if self.default_lang not in SUPPORTED_LANGS:
            self.default_lang = "ko"
    
    async def dispatch(self, request: Request, call_next):
        """
        요청 처리 및 언어 감지.
        
        Args:
            request: FastAPI Request 객체
            call_next: 다음 미들웨어/핸들러
        
        Returns:
            Response with X-Resolved-Lang header
        """
        # 언어 감지
        lang = self._detect_request_language(request)
        
        # request.state에 저장
        request.state.route_lang = lang
        
        # 다음 핸들러 호출
        response = await call_next(request)
        
        # 응답 헤더에 감지된 언어 추가
        response.headers["X-Resolved-Lang"] = lang
        
        return response
    
    def _detect_request_language(self, request: Request) -> str:
        """
        요청에서 언어 감지.
        
        우선순위:
            1. 쿼리 파라미터 ?lang=
            2. 헤더 X-Lang
            3. Accept-Language 헤더
            4. 쿠키 lang
            5. JWT 클레임 pref_lang (request.state.user.pref_lang)
            6. 기본값
        
        Args:
            request: FastAPI Request 객체
        
        Returns:
            감지된 언어 코드
        """
        # 1. 강제 언어 (쿼리 파라미터 또는 헤더)
        forced_lang = (
            request.query_params.get("lang") or
            request.headers.get("x-lang") or
            request.headers.get("X-Lang")
        )
        
        # 2. Accept-Language 헤더
        accept_language = request.headers.get("accept-language")
        
        # 3. 쿠키
        cookie_lang = request.cookies.get("lang")
        
        # 4. JWT 클레임 (선택)
        jwt_lang = None
        user = getattr(request.state, "user", None)
        if user:
            jwt_lang = getattr(user, "pref_lang", None) or getattr(user, "lang", None)
        
        # 언어 감지
        return detect_language(
            accept_language=accept_language,
            forced_lang=forced_lang,
            cookie_lang=cookie_lang,
            jwt_lang=jwt_lang,
            default=self.default_lang
        )


def get_request_language(request: Request) -> str:
    """
    요청에서 감지된 언어 가져오기.
    
    Args:
        request: FastAPI Request 객체
    
    Returns:
        감지된 언어 코드 (기본값: 'ko')
    
    Example:
        >>> from fastapi import Request, Depends
        >>> from shared.llm.middleware import get_request_language
        >>> 
        >>> @app.get("/test")
        >>> async def test(lang: str = Depends(get_request_language)):
        ...     return {"language": lang}
    """
    return getattr(request.state, "route_lang", "ko")
