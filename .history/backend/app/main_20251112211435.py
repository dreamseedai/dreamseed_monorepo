"""
DreamSeed Backend - Phase 1 MVP + Trust Chain
FastAPI Application with Authentication & Trustworthy AI Stack
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, problems, submissions, progress, questions
from app.api.routers import explain, feedback, provenance, audit
from app.middleware import PIIFilterMiddleware, RequestAuditMiddleware

app = FastAPI(
    title="DreamSeed API - Trust Chain Enabled",
    description="Phase 1 MVP - 적응형 학습 플랫폼 + 신뢰할 수 있는 AI 스택",
    version="1.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Trust Chain Middleware (순서 중요!)
# 1. 감사 로깅 (모든 요청 추적)
app.add_middleware(RequestAuditMiddleware, enabled=True)
# 2. PII 필터링 (응답 데이터 마스킹)
app.add_middleware(PIIFilterMiddleware, enabled=True)

# CORS 설정
origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5172,http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 기존 라우터
app.include_router(auth.router, prefix="/api/seedtest")
app.include_router(problems.router, prefix="/api/seedtest")
app.include_router(submissions.router, prefix="/api/seedtest")
app.include_router(progress.router, prefix="/api/seedtest")
app.include_router(questions.router, prefix="/api/seedtest")

# Trust Chain 라우터
app.include_router(explain.router, prefix="/api/trust/explain", tags=["Trust-Explainability"])
app.include_router(feedback.router, prefix="/api/trust/feedback", tags=["Trust-Feedback"])
app.include_router(provenance.router, prefix="/api/trust/provenance", tags=["Trust-Provenance"])
app.include_router(audit.router, prefix="/api/trust/audit", tags=["Trust-Audit"])


@app.get("/")
def root():
    """API 루트 엔드포인트"""
    return {
        "message": "DreamSeed API - Phase 1 MVP + Trust Chain",
        "version": "1.1.0",
        "status": "operational",
        "trust_chain": {
            "data_minimization": "enabled",
            "provenance_tracking": "enabled",
            "explainability": "enabled",
            "feedback_loops": "enabled",
            "audit_visibility": "enabled"
        }
    }


@app.get("/api/seedtest/meta")
def get_meta():
    """API 메타 정보"""
    return {
        "api_prefix": "/api/seedtest",
        "legacy_readonly_enabled": False,
        "legacy_source": "postgres",
        "features": {
            "idempotency": False,
            "if_match_required": False
        }
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
