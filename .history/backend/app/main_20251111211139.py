"""
DreamSeed Backend - Phase 1 MVP
FastAPI Application with Authentication
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth

app = FastAPI(
    title="DreamSeed API",
    description="Phase 1 MVP - 적응형 학습 플랫폼",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 특정 도메인으로 제한
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """API 루트 엔드포인트"""
    return {"message": "DreamSeedAI Backend API", "version": "1.0.0", "status": "running"}


@app.get("/health")
async def health_check():
    """헬스 체크 엔드포인트"""
    return {"status": "healthy"}


# 라우터 등록 (기존 API들을 통합할 때 사용)
# app.include_router(assignment_api.router, prefix="/api/assignments", tags=["assignments"])
# app.include_router(question_display_api.router, prefix="/api/questions", tags=["questions"])

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
