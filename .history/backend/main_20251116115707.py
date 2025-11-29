"""
DreamSeed Backend - Phase 1 MVP
FastAPI application with AI feedback capabilities
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.ai_feedback import router as ai_router
from app.api.payment import router as payment_router
from app.api.questions import router as questions_router

app = FastAPI(title="DreamSeed Phase 1 Backend")

# CORS settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5172", "http://localhost:3030", "http://localhost:3031"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(ai_router)
app.include_router(payment_router)
app.include_router(questions_router)


@app.get("/")
async def root():
    return {
        "message": "DreamSeed API - Phase 1 MVP",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    return {"status": "healthy", "phase": "Phase 1 MVP"}


@app.get("/api/admin/meta")
async def get_meta():
    """
    메타 정보 엔드포인트 - legacy readonly 모드 등
    """
    return {
        "legacy_readonly_enabled": False,
        "legacy_source": None
    }
