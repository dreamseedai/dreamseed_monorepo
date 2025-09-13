from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import uuid
from datetime import datetime
import httpx

app = FastAPI(
    title="AI Orchestrator",
    description="API for routing requests to language and domain-specific LLMs",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AIRequest(BaseModel):
    type: str  # 'career-guidance', 'learning-recommendation', 'content-generation'
    context: Dict[str, Any]
    user_id: str

class AIResponse(BaseModel):
    type: str
    data: Any
    confidence: float
    metadata: Optional[Dict[str, Any]] = None

# Mock LLM routing configuration
LLM_ROUTES = {
    "career-guidance": {
        "model": "career-advisor-llm",
        "endpoint": "http://localhost:9001/generate",
        "specialty": "Career planning and professional development"
    },
    "learning-recommendation": {
        "model": "learning-optimizer-llm", 
        "endpoint": "http://localhost:9002/generate",
        "specialty": "Educational content and learning paths"
    },
    "content-generation": {
        "model": "content-creator-llm",
        "endpoint": "http://localhost:9003/generate", 
        "specialty": "Educational content creation"
    }
}

@app.get("/")
async def root():
    return {"message": "AI Orchestrator is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}

@app.get("/models")
async def get_available_models():
    """Get list of available AI models and their specialties"""
    return {
        "models": [
            {
                "type": route_type,
                "model": config["model"],
                "specialty": config["specialty"],
                "status": "available"  # In production, check actual service health
            }
            for route_type, config in LLM_ROUTES.items()
        ]
    }

@app.post("/generate")
async def generate_ai_response(request: AIRequest) -> AIResponse:
    """Route AI request to appropriate LLM and return response"""
    
    if request.type not in LLM_ROUTES:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported AI request type: {request.type}"
        )
    
    route_config = LLM_ROUTES[request.type]
    
    # For demo purposes, return mock responses instead of calling external LLMs
    mock_response = await _generate_mock_response(request)
    
    return AIResponse(
        type=request.type,
        data=mock_response,
        confidence=0.85,
        metadata={
            "model_used": route_config["model"],
            "processing_time_ms": 1200,
            "request_id": str(uuid.uuid4())
        }
    )

async def _generate_mock_response(request: AIRequest) -> Dict[str, Any]:
    """Generate mock AI responses based on request type"""
    
    if request.type == "career-guidance":
        return {
            "recommendations": [
                "Focus on building strong programming fundamentals",
                "Consider specializing in cloud technologies",
                "Develop soft skills through team projects"
            ],
            "next_steps": [
                "Complete Python fundamentals course",
                "Build a portfolio project",
                "Network with industry professionals"
            ],
            "timeline": "3-6 months for foundational skills"
        }
    
    elif request.type == "learning-recommendation":
        user_skills = request.context.get("current_skills", [])
        career_goal = request.context.get("career_goal", "software developer")
        
        return {
            "recommended_modules": [
                {
                    "title": "Advanced Python Programming",
                    "reason": "Builds on your current Python knowledge",
                    "priority": "high"
                },
                {
                    "title": "Database Design Fundamentals", 
                    "reason": "Essential for backend development",
                    "priority": "medium"
                }
            ],
            "learning_path": f"Customized path for {career_goal}",
            "estimated_duration": "4-8 weeks"
        }
    
    elif request.type == "content-generation":
        topic = request.context.get("topic", "programming")
        content_type = request.context.get("content_type", "article")
        
        return {
            "generated_content": f"# Introduction to {topic}\n\nThis {content_type} covers the fundamental concepts...",
            "content_type": content_type,
            "topic": topic,
            "word_count": 250,
            "reading_time": "2 minutes"
        }
    
    else:
        return {"message": "Response generated successfully"}

@app.post("/batch-generate")
async def batch_generate(requests: List[AIRequest]) -> List[AIResponse]:
    """Process multiple AI requests in batch"""
    responses = []
    
    for request in requests:
        try:
            response = await generate_ai_response(request)
            responses.append(response)
        except Exception as e:
            # In production, handle errors more gracefully
            error_response = AIResponse(
                type=request.type,
                data={"error": str(e)},
                confidence=0.0,
                metadata={"error": True}
            )
            responses.append(error_response)
    
    return responses

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)