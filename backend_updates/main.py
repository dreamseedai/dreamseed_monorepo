
# Main FastAPI app updates
from fastapi import FastAPI
from routes.questions import router as questions_router
from routes.adaptive_learning import router as adaptive_router

app = FastAPI(
    title="DreamSeedAI API",
    description="Enhanced API with adaptive learning and multilingual support",
    version="2.0.0"
)

# Include routers
app.include_router(questions_router, prefix="/api/v2/questions", tags=["questions"])
app.include_router(adaptive_router, prefix="/api/v2/learning", tags=["adaptive_learning"])

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "2.0.0"}
