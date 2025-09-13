from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uuid
from datetime import datetime

app = FastAPI(
    title="Progress API",
    description="API for tracking user learning progress",
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

class ProgressUpdate(BaseModel):
    completion_percentage: int
    time_spent: int  # in minutes

# Mock data for demo
progress_db = [
    {
        "id": str(uuid.uuid4()),
        "userId": "user-123",
        "moduleId": "module-456",
        "status": "in-progress",
        "completionPercentage": 45,
        "timeSpent": 30,
        "lastAccessed": datetime.utcnow()
    },
    {
        "id": str(uuid.uuid4()),
        "userId": "user-123",
        "moduleId": "module-789",
        "status": "completed",
        "completionPercentage": 100,
        "timeSpent": 60,
        "lastAccessed": datetime.utcnow()
    }
]

@app.get("/")
async def root():
    return {"message": "Progress API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}

@app.get("/progress/{user_id}")
async def get_user_progress(user_id: str):
    """Get all progress records for a user"""
    user_progress = [p for p in progress_db if p["userId"] == user_id]
    return {"user_id": user_id, "progress": user_progress}

@app.get("/progress/{user_id}/{module_id}")
async def get_module_progress(user_id: str, module_id: str):
    """Get progress for a specific user and module"""
    progress = next(
        (p for p in progress_db if p["userId"] == user_id and p["moduleId"] == module_id),
        None
    )
    if not progress:
        raise HTTPException(status_code=404, detail="Progress record not found")
    return progress

@app.post("/progress/{user_id}/{module_id}")
async def update_progress(user_id: str, module_id: str, progress_update: ProgressUpdate):
    """Update progress for a user and module"""
    # Find existing progress record
    progress_index = next(
        (i for i, p in enumerate(progress_db) 
         if p["userId"] == user_id and p["moduleId"] == module_id),
        None
    )
    
    if progress_index is not None:
        # Update existing record
        progress_db[progress_index].update({
            "completionPercentage": progress_update.completion_percentage,
            "timeSpent": progress_update.time_spent,
            "status": "completed" if progress_update.completion_percentage == 100 else "in-progress",
            "lastAccessed": datetime.utcnow()
        })
        return progress_db[progress_index]
    else:
        # Create new record
        new_progress = {
            "id": str(uuid.uuid4()),
            "userId": user_id,
            "moduleId": module_id,
            "status": "completed" if progress_update.completion_percentage == 100 else "in-progress",
            "completionPercentage": progress_update.completion_percentage,
            "timeSpent": progress_update.time_spent,
            "lastAccessed": datetime.utcnow()
        }
        progress_db.append(new_progress)
        return new_progress

@app.get("/analytics/{user_id}")
async def get_user_analytics(user_id: str):
    """Get analytics for a user's learning progress"""
    user_progress = [p for p in progress_db if p["userId"] == user_id]
    
    if not user_progress:
        return {
            "user_id": user_id,
            "total_modules": 0,
            "completed_modules": 0,
            "in_progress_modules": 0,
            "total_time_spent": 0,
            "average_completion": 0
        }
    
    completed_modules = len([p for p in user_progress if p["status"] == "completed"])
    in_progress_modules = len([p for p in user_progress if p["status"] == "in-progress"])
    total_time_spent = sum(p["timeSpent"] for p in user_progress)
    average_completion = sum(p["completionPercentage"] for p in user_progress) / len(user_progress)
    
    return {
        "user_id": user_id,
        "total_modules": len(user_progress),
        "completed_modules": completed_modules,
        "in_progress_modules": in_progress_modules,
        "total_time_spent": total_time_spent,
        "average_completion": round(average_completion, 2)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)