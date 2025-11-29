"""
DreamSeed Backend - Phase 1 MVP
FastAPI application with AI feedback capabilities
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.ai_feedback import router as ai_router

app = FastAPI(
    title="DreamSeed API",
    description="Phase 1 MVP - Educational Platform with AI Feedback",
    version="1.0.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5172", "http://localhost:3030", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(ai_router)


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
