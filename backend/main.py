"""
DreamSeed Backend - Phase 1 MVP
FastAPI application with AI feedback capabilities
"""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.ai_feedback import router as ai_router
from app.api.payment import router as payment_router
from app.api.questions import router as questions_router
from app.api.teachers import router as teachers_router
from app.api.parents import router as parents_router
from app.api.tutors import router as tutors_router
from app.api.routers.dashboard import router as dashboard_router
from app.api.routers.classes import router as classes_router
from app.api.routers.adaptive_exam import router as adaptive_exam_router
from app.api.routers.auth import router as auth_router
from app.api.routers.week3_exams import exams_router, sessions_router
from app.api.routers.teacher_class import router as teacher_class_router
from app.api.routers.parent_portal import router as parent_portal_router
from app.api.routers.parent_reports import router as parent_reports_router
from app.routers.messenger import router as messenger_router
from app.routers.assignments import router as assignments_router
from app.messenger.broadcaster import start_broadcaster, stop_broadcaster
from app.messenger.presence import presence_cleanup_task

logger = logging.getLogger(__name__)

app = FastAPI(title="DreamSeed Phase 1 Backend")

# CORS settings - 4개 포털 + 관리자 페이지
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5172",  # portal_front (메인 포털)
        "http://localhost:3001",  # student_front
        "http://localhost:3002",  # teacher_front
        "http://localhost:3003",  # tutor_front
        "http://localhost:3004",  # parent_front
        "http://localhost:3000",  # admin_front
        # Production: https://*.dreamseedai.com
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)  # Authentication (register, login, logout)
app.include_router(exams_router, prefix="/api")  # Week 3: Exam Flow
app.include_router(sessions_router, prefix="/api")  # Week 3: Exam Sessions
app.include_router(ai_router)
app.include_router(payment_router)
app.include_router(questions_router)
app.include_router(teachers_router)
app.include_router(parents_router)
app.include_router(tutors_router)
app.include_router(dashboard_router)  # Teacher/Parent dashboard APIs
app.include_router(classes_router)  # Class management and statistics
app.include_router(adaptive_exam_router)  # Adaptive CAT exam with IRT engine

# Week 4: Portal-specific APIs
app.include_router(teacher_class_router)  # GET /api/teacher/class-list
app.include_router(parent_portal_router)  # GET /api/parent/children
app.include_router(parent_reports_router)  # GET /api/parent/reports/{id}/pdf

# Messenger system
app.include_router(messenger_router)  # Real-time messaging

# Assignment (homework) management system
app.include_router(
    assignments_router, prefix="/api"
)  # Assignment and submission management


@app.on_event("startup")
async def startup():
    """Application startup event - initialize messenger broadcaster and presence system"""
    import asyncio

    try:
        await start_broadcaster()
        logger.info("Messenger broadcaster started successfully")
    except Exception as e:
        logger.error(f"Failed to start messenger broadcaster: {e}")

    try:
        # Start presence cleanup background task
        asyncio.create_task(presence_cleanup_task())
        logger.info("Presence cleanup task started successfully")
    except Exception as e:
        logger.error(f"Failed to start presence cleanup task: {e}")


@app.on_event("shutdown")
async def shutdown():
    """Application shutdown event - cleanup messenger broadcaster"""
    try:
        await stop_broadcaster()
        logger.info("Messenger broadcaster stopped successfully")
    except Exception as e:
        logger.error(f"Failed to stop messenger broadcaster: {e}")


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
    return {"legacy_readonly_enabled": False, "legacy_source": None}
