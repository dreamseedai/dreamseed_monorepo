"""
DreamSeed Backend - Phase 1 MVP
FastAPI Application with Authentication
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, problems

app = FastAPI(
    title="DreamSeed API",
    description="Phase 1 MVP - 적응형 학습 플랫폼",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS 설정
origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(auth.router)
app.include_router(problems.router)


@app.get("/")
def root():
    """API 루트 엔드포인트"""
    return {
        "message": "DreamSeed API - Phase 1 MVP",
        "version": "1.0.0",
        "status": "operational"
    }


@app.get("/health")
def health_check():
    """헬스 체크 엔드포인트"""
    return {
        "status": "healthy",
        "database": "connected"
    }

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
