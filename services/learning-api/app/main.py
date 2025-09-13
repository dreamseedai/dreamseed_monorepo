from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import uuid
from datetime import datetime

app = FastAPI(
    title="Learning API",
    description="API for managing learning modules and content",
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
learning_modules_db = [
    {
        "id": str(uuid.uuid4()),
        "title": "Introduction to React",
        "description": "Learn the basics of React components and JSX",
        "content": "React is a JavaScript library for building user interfaces...",
        "type": "article",
        "duration": 45,
        "difficulty": "beginner",
        "tags": ["javascript", "react", "frontend"]
    },
    {
        "id": str(uuid.uuid4()),
        "title": "Python Data Structures",
        "description": "Master lists, dictionaries, and sets in Python",
        "content": "Python provides several built-in data structures...",
        "type": "video",
        "duration": 60,
        "difficulty": "beginner",
        "tags": ["python", "data-structures", "programming"]
    },
    {
        "id": str(uuid.uuid4()),
        "title": "Docker Fundamentals",
        "description": "Learn containerization with Docker",
        "content": "Docker is a platform for developing, shipping, and running applications...",
        "type": "exercise",
        "duration": 90,
        "difficulty": "intermediate",
        "tags": ["docker", "devops", "containers"]
    }
]

@app.get("/")
async def root():
    return {"message": "Learning API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}

@app.get("/modules")
async def get_learning_modules(
    difficulty: Optional[str] = None,
    type: Optional[str] = None,
    tags: Optional[List[str]] = None
):
    """Get learning modules with optional filters"""
    modules = learning_modules_db.copy()
    
    if difficulty:
        modules = [m for m in modules if m["difficulty"] == difficulty]
    
    if type:
        modules = [m for m in modules if m["type"] == type]
    
    if tags:
        modules = [m for m in modules if any(tag in m["tags"] for tag in tags)]
    
    return {"modules": modules}

@app.get("/modules/{module_id}")
async def get_learning_module(module_id: str):
    """Get a specific learning module by ID"""
    module = next((m for m in learning_modules_db if m["id"] == module_id), None)
    if not module:
        raise HTTPException(status_code=404, detail="Learning module not found")
    return module

@app.post("/modules/{module_id}/start")
async def start_module(module_id: str, user_id: str):
    """Start a learning module for a user"""
    module = next((m for m in learning_modules_db if m["id"] == module_id), None)
    if not module:
        raise HTTPException(status_code=404, detail="Learning module not found")
    
    return {
        "message": f"Started module '{module['title']}' for user {user_id}",
        "module": module,
        "started_at": datetime.utcnow()
    }

@app.get("/modules/search")
async def search_modules(query: str):
    """Search learning modules by title, description, or tags"""
    query_lower = query.lower()
    matching_modules = [
        m for m in learning_modules_db
        if query_lower in m["title"].lower() 
        or query_lower in m["description"].lower()
        or any(query_lower in tag.lower() for tag in m["tags"])
    ]
    
    return {"query": query, "modules": matching_modules}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)