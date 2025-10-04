from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uvicorn
import secrets

# Pydantic models matching frontend types
class Country(str):
    US = "US"
    CA = "CA"
    KR = "KR"
    CN = "CN"

class Grade(str):
    G9 = "G9"
    G10 = "G10"
    G11 = "G11"
    G12 = "G12"

class Goal(str):
    SAT_1500_PLUS = "SAT_1500_PLUS"
    AP_5 = "AP_5"
    COLLEGE_ADMISSIONS = "COLLEGE_ADMISSIONS"
    TOEFL_IELTS = "TOEFL_IELTS"

class UserProfile(BaseModel):
    userId: str
    country: str
    grade: str
    goals: List[str]
    languages: List[str]
    history: Optional[Dict[str, Any]] = None

class DiagnosticRequest(BaseModel):
    userId: str
    context: Dict[str, str]  # country, grade, goal
    evidence: Optional[Dict[str, Any]] = None

class DiagnosticResponse(BaseModel):
    userId: str
    summary: str
    weaknesses: List[str]
    recommendedModules: List[str]
    recommendedProblems: List[Dict[str, str]]
    nextWeekPlan: List[Dict[str, Any]]
    tokenUsage: Optional[Dict[str, int]] = None

# Share API models
class ShareIn(BaseModel):
    payload: Dict[str, Any]

class ShareOut(BaseModel):
    id: str
    url: str

# In-memory store for share data (demo)
SHARE_STORE: Dict[str, Dict[str, Any]] = {}

# FastAPI app
app = FastAPI(
    title="DreamSeedAI API",
    description="AI-powered educational platform API",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://dreamseedai.com",
        "https://staging.dreamseedai.com",
        "http://localhost:5173",
        "http://localhost:3000"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    max_age=600,
)

@app.get("/")
async def root():
    return {"message": "DreamSeedAI API is running"}

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "dreamseed-api"}

@app.post("/api/diagnostics/run", response_model=DiagnosticResponse)
async def run_diagnostics(request: DiagnosticRequest):
    """
    Run diagnostics for user based on their profile and goals
    """
    try:
        # Extract context
        country = request.context.get("country", "US")
        grade = request.context.get("grade", "G11")
        goal = request.context.get("goal", "SAT_1500_PLUS")
        
        # Demo logic based on goal
        is_sat = goal.startswith("SAT") or "SAT" in goal
        is_ap = "AP" in goal
        is_toefl = "TOEFL" in goal or "IELTS" in goal
        
        # Generate weaknesses based on goal
        if is_sat:
            weaknesses = ["algebraic_manipulation", "reading_inference", "time_management"]
            recommended_modules = ["Math", "English / ELA", "Exams & Admissions"]
            recommended_problems = [
                {"id": "sat-math-001", "title": "Quadratic completion practice"},
                {"id": "sat-rw-014", "title": "Paired passages: inference & evidence"},
                {"id": "sat-math-045", "title": "Systems of equations word problems"}
            ]
        elif is_ap:
            weaknesses = ["concept_application", "essay_structure", "time_pressure"]
            recommended_modules = ["AP Courses", "Test Prep", "Writing"]
            recommended_problems = [
                {"id": "ap-bio-001", "title": "Cell structure and function"},
                {"id": "ap-chem-012", "title": "Stoichiometry calculations"},
                {"id": "ap-lang-008", "title": "Rhetorical analysis essay"}
            ]
        elif is_toefl:
            weaknesses = ["listening_comprehension", "speaking_fluency", "academic_vocabulary"]
            recommended_modules = ["English", "Test Prep", "Speaking"]
            recommended_problems = [
                {"id": "toefl-list-001", "title": "Academic lecture comprehension"},
                {"id": "toefl-speak-003", "title": "Independent speaking practice"},
                {"id": "toefl-read-015", "title": "Academic reading passages"}
            ]
        else:
            weaknesses = ["general_preparation", "test_strategy", "time_management"]
            recommended_modules = ["Test Prep", "Study Skills", "Exams & Admissions"]
            recommended_problems = [
                {"id": "gen-prep-001", "title": "General test preparation"},
                {"id": "gen-strat-002", "title": "Test-taking strategies"},
                {"id": "gen-time-003", "title": "Time management practice"}
            ]
        
        # Generate next week plan
        next_week_plan = [
            {
                "day": "Monday",
                "tasks": [
                    f"30m {goal} practice session",
                    "Review previous mistakes",
                    "Set weekly goals"
                ]
            },
            {
                "day": "Wednesday", 
                "tasks": [
                    f"Mock {goal} section practice",
                    "Focus on identified weaknesses",
                    "Track progress"
                ]
            },
            {
                "day": "Saturday",
                "tasks": [
                    f"Full-length {goal} practice test",
                    "Post-test analysis and review",
                    "Plan next week's focus areas"
                ]
            }
        ]
        
        # Generate summary
        summary = f"Diagnostic completed for {country}/{grade} student. Goal: {goal}. "
        summary += f"Identified {len(weaknesses)} key areas for improvement. "
        summary += f"Recommended {len(recommended_modules)} learning modules and {len(recommended_problems)} practice problems."
        
        return DiagnosticResponse(
            userId=request.userId,
            summary=summary,
            weaknesses=weaknesses,
            recommendedModules=recommended_modules,
            recommendedProblems=recommended_problems,
            nextWeekPlan=next_week_plan,
            tokenUsage={
                "prompt": 0,
                "completion": 0,
                "total": 0
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Diagnostic processing failed: {str(e)}")

@app.get("/api/profile/{user_id}")
async def get_profile(user_id: str):
    """
    Get user profile by ID (demo implementation)
    """
    return {
        "userId": user_id,
        "country": "US",
        "grade": "G11", 
        "goals": ["SAT_1500_PLUS"],
        "languages": ["en"],
        "history": {
            "sat": [
                {"math": 650, "rw": 600, "date": "2024-09-15"}
            ]
        }
    }

@app.post("/api/profile")
async def create_or_update_profile(profile: UserProfile):
    """
    Create or update user profile
    """
    return {
        "message": "Profile updated successfully",
        "profile": profile
    }

# Share API endpoints
@app.post("/api/share", response_model=ShareOut)
async def create_share(item: ShareIn):
    """
    Create a shareable link for plan data
    """
    try:
        sid = secrets.token_urlsafe(6)  # short-ish id
        SHARE_STORE[sid] = item.payload
        return ShareOut(id=sid, url=f"/api/share/{sid}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Share creation failed: {str(e)}")

@app.get("/api/share/{sid}")
async def get_share(sid: str):
    """
    Retrieve shared data by ID
    """
    if sid not in SHARE_STORE:
        raise HTTPException(status_code=404, detail="Share not found")
    return SHARE_STORE[sid]

if __name__ == "__main__":
    # For local development
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)

# curl test example:
# curl -X POST http://localhost:8000/api/diagnostics/run \
#   -H 'Content-Type: application/json' \
#   -d '{"userId":"u123","context":{"country":"US","grade":"G11","goal":"SAT_1500_PLUS"}}'


