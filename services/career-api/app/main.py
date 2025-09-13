from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import uuid
from datetime import datetime

app = FastAPI(
    title="Career API",
    description="API for managing career paths and guidance",
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

# Mock data for demo
career_paths_db = [
    {
        "id": str(uuid.uuid4()),
        "title": "Full Stack Developer",
        "description": "Learn both frontend and backend development",
        "requiredSkills": ["JavaScript", "React", "Node.js", "Python", "SQL"],
        "estimatedDuration": "6-12 months",
        "difficulty": "intermediate"
    },
    {
        "id": str(uuid.uuid4()),
        "title": "Data Scientist",
        "description": "Master data analysis and machine learning",
        "requiredSkills": ["Python", "R", "SQL", "Machine Learning", "Statistics"],
        "estimatedDuration": "8-15 months",
        "difficulty": "advanced"
    },
    {
        "id": str(uuid.uuid4()),
        "title": "DevOps Engineer",
        "description": "Learn infrastructure and deployment automation",
        "requiredSkills": ["Docker", "Kubernetes", "AWS", "Linux", "CI/CD"],
        "estimatedDuration": "4-8 months",
        "difficulty": "intermediate"
    }
]

@app.get("/")
async def root():
    return {"message": "Career API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}

@app.get("/career-paths")
async def get_career_paths():
    """Get all available career paths"""
    return {"career_paths": career_paths_db}

@app.get("/career-paths/{path_id}")
async def get_career_path(path_id: str):
    """Get a specific career path by ID"""
    path = next((p for p in career_paths_db if p["id"] == path_id), None)
    if not path:
        raise HTTPException(status_code=404, detail="Career path not found")
    return path

@app.post("/career-paths/{path_id}/recommend")
async def get_career_recommendations(path_id: str, user_skills: List[str]):
    """Get personalized recommendations for a career path"""
    path = next((p for p in career_paths_db if p["id"] == path_id), None)
    if not path:
        raise HTTPException(status_code=404, detail="Career path not found")
    
    required_skills = set(path["requiredSkills"])
    user_skills_set = set(user_skills)
    missing_skills = required_skills - user_skills_set
    
    return {
        "career_path": path,
        "missing_skills": list(missing_skills),
        "completion_percentage": round((len(user_skills_set & required_skills) / len(required_skills)) * 100, 2),
        "next_steps": list(missing_skills)[:3] if missing_skills else ["Continue practicing current skills"]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)