"""
Assignment API for Teacher Dashboard
FastAPI endpoint that receives student lists and assignment templates
"""
from datetime import datetime
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel

app = FastAPI(title="Assignment API", version="1.0.0")

# ---------------------------
# Models
# ---------------------------
class AssignmentRequest(BaseModel):
    student_ids: List[str]
    template: str  # remedial_basics, supplementary_review, core_practice, challenge_advanced, enrichment_extension
    assigned_by: str
    org_id: str
    timestamp: str
    due_date: Optional[str] = None
    notes: Optional[str] = None


class AssignmentResponse(BaseModel):
    assignment_id: str
    student_ids: List[str]
    template: str
    created_at: str
    status: str


# ---------------------------
# Template mapping
# ---------------------------
ASSIGNMENT_TEMPLATES = {
    "remedial_basics": {
        "title": "기본 개념 보정 과제",
        "description": "기초 개념을 다시 학습하고 연습문제를 풉니다.",
        "difficulty": "easy",
        "estimated_time_minutes": 30,
        "content_tags": ["기본개념", "보정학습", "기초문제"]
    },
    "supplementary_review": {
        "title": "보충 복습 과제",
        "description": "최근 학습 내용을 복습하고 유사 문제를 풉니다.",
        "difficulty": "medium",
        "estimated_time_minutes": 45,
        "content_tags": ["복습", "보충학습", "응용문제"]
    },
    "core_practice": {
        "title": "핵심 연습 과제",
        "description": "핵심 개념을 강화하고 다양한 유형을 연습합니다.",
        "difficulty": "medium",
        "estimated_time_minutes": 60,
        "content_tags": ["핵심개념", "문제유형", "실전연습"]
    },
    "challenge_advanced": {
        "title": "상향 도전 과제",
        "description": "심화 문제를 풀고 상위 수준 개념을 학습합니다.",
        "difficulty": "hard",
        "estimated_time_minutes": 75,
        "content_tags": ["심화학습", "도전문제", "상위개념"]
    },
    "enrichment_extension": {
        "title": "심화 확장 과제",
        "description": "확장 주제를 탐구하고 창의적 문제를 해결합니다.",
        "difficulty": "advanced",
        "estimated_time_minutes": 90,
        "content_tags": ["확장학습", "창의문제", "탐구활동"]
    }
}


# ---------------------------
# Endpoints
# ---------------------------
@app.post("/api/assignments", response_model=AssignmentResponse)
async def create_assignment(
    req: AssignmentRequest,
    x_user: str = Header(None, alias="X-User"),
    x_org_id: str = Header(None, alias="X-Org-Id")
):
    """
    Create a new assignment for a list of students
    
    Request body:
    - student_ids: List of student IDs
    - template: Assignment template key
    - assigned_by: Teacher user ID
    - org_id: Organization ID
    - timestamp: ISO8601 timestamp
    - due_date: Optional due date
    - notes: Optional teacher notes
    
    Returns:
    - assignment_id: Unique assignment ID
    - student_ids: List of students assigned
    - template: Template used
    - created_at: Creation timestamp
    - status: Assignment status
    """
    
    # Validate template
    if req.template not in ASSIGNMENT_TEMPLATES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid template: {req.template}. Valid templates: {list(ASSIGNMENT_TEMPLATES.keys())}"
        )
    
    # Validate org_id matches header
    if x_org_id and req.org_id != x_org_id:
        raise HTTPException(status_code=403, detail="org_id mismatch")
    
    # Generate assignment ID
    assignment_id = f"ASG_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{req.org_id}"
    
    # Here you would typically:
    # 1. Insert into database
    # 2. Trigger notification to students
    # 3. Create assignment records
    # 4. Log the action
    
    # For demo, just return success
    print(f"[assignment API] Created assignment {assignment_id}")
    print(f"  Template: {req.template} - {ASSIGNMENT_TEMPLATES[req.template]['title']}")
    print(f"  Students: {len(req.student_ids)} students")
    print(f"  Assigned by: {req.assigned_by}")
    print(f"  Org: {req.org_id}")
    
    return AssignmentResponse(
        assignment_id=assignment_id,
        student_ids=req.student_ids,
        template=req.template,
        created_at=datetime.utcnow().isoformat() + "Z",
        status="created"
    )


@app.get("/api/assignments/{assignment_id}")
async def get_assignment(assignment_id: str):
    """Get assignment details by ID"""
    # Placeholder: fetch from database
    return {
        "assignment_id": assignment_id,
        "status": "created",
        "message": "Assignment API is working"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "service": "assignment-api"}


# ---------------------------
# Run with: uvicorn assignment_api:app --host 0.0.0.0 --port 8000 --reload
# ---------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
