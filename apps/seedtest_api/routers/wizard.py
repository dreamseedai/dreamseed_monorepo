"""
Tutor Onboarding Wizard API
Simplified exam creation for first-time tutors (V1 TTFP optimization)
"""
from typing import Any
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ..security.jwt import require_scopes
from ..services.adaptive_engine import start_session
from ..settings import settings

router = APIRouter(prefix=f"{settings.API_PREFIX}/wizard", tags=["wizard"])


class QuickStartRequest(BaseModel):
    """Minimal input for tutor's first exam"""
    tutor_name: str = Field(..., min_length=1, max_length=100, description="Tutor or school name")
    subject: str = Field(default="Math", description="Subject: Math, English, Science")
    grade_level: str = Field(default="G10", description="Grade level: G9, G10, G11, G12")
    num_questions: int = Field(default=10, ge=5, le=25, description="Number of questions (5-25)")
    difficulty: str = Field(default="medium", description="Difficulty: easy, medium, hard")


class QuickStartResponse(BaseModel):
    """Response with session details and next steps"""
    session_id: str
    exam_id: str
    pdf_url: str
    dashboard_url: str
    next_steps: list[str]
    estimated_time_minutes: int


def _map_subject_to_exam_id(subject: str) -> str:
    """Map friendly subject name to internal exam_id"""
    subject_lower = subject.lower().strip()
    mapping = {
        "math": "math_adaptive",
        "mathematics": "math_adaptive",
        "english": "english_adaptive",
        "science": "science_adaptive",
        "physics": "science_adaptive",
        "chemistry": "science_adaptive",
    }
    return mapping.get(subject_lower, "math_adaptive")


def _difficulty_to_initial_theta(difficulty: str) -> float:
    """Map difficulty level to initial IRT theta (ability estimate)"""
    difficulty_lower = difficulty.lower().strip()
    mapping = {
        "easy": -1.0,  # Below average
        "medium": 0.0,  # Average
        "hard": 1.0,   # Above average
    }
    return mapping.get(difficulty_lower, 0.0)


@router.post(
    "/quick-start",
    response_model=QuickStartResponse,
    summary="Quick-start wizard for tutors (V1)",
    description=(
        "Simplified exam creation for first-time tutors.\n\n"
        "Creates an adaptive exam session with sensible defaults based on minimal input.\n"
        "Returns session ID and direct PDF download URL.\n\n"
        "V1 optimization: Minimizes TTFP (Time to First PDF) by auto-filling exam settings."
    ),
)
async def quick_start_wizard(
    req: QuickStartRequest,
    payload=Depends(require_scopes("exam:write")),
) -> QuickStartResponse:
    """
    Create first exam for tutor with one-click simplicity.
    
    Flow:
    1. Map subject → exam_id (e.g., "Math" → "math_adaptive")
    2. Create exam session with user's org_id
    3. (Optional) Pre-seed initial questions based on difficulty
    4. Return PDF URL for instant download
    """
    user_id = payload.get("sub", "wizard_user")
    org_id = int(payload.get("org_id", -1))
    
    if org_id < 0:
        raise HTTPException(403, "Organization ID required (missing from token)")
    
    # Map friendly inputs to internal values
    exam_id = _map_subject_to_exam_id(req.subject)
    # Note: initial_theta from difficulty could be used for pre-seeding questions (V2)
    # initial_theta = _difficulty_to_initial_theta(req.difficulty)
    
    # Create exam session (reuse existing adaptive engine)
    try:
        session_response = start_session(
            exam_id=exam_id,
            user_id=user_id,
            org_id=org_id,
        )
        session_id = session_response.get("exam_session_id")
        
        if not session_id:
            raise HTTPException(500, "Failed to create exam session")
    
    except Exception as e:
        raise HTTPException(500, f"Exam creation failed: {str(e)}")
    
    # Build response URLs
    tutor_name_encoded = quote(req.tutor_name)
    pdf_url = f"/api/seedtest/exams/{session_id}/result/pdf?brand={tutor_name_encoded}"
    dashboard_url = f"/tutor/dashboard?session={session_id}"  # Frontend route
    
    # Generate next steps based on V1 flow
    next_steps = [
        f"📝 Have a student complete the {req.num_questions}-question {req.subject} exam",
        f"📊 Review results at {dashboard_url}",
        f"📄 Download PDF report: {pdf_url}",
        "👥 Assign to more students from your dashboard",
    ]
    
    # Estimate time: ~2 min/question + 5 min review
    estimated_time_minutes = req.num_questions * 2 + 5
    
    return QuickStartResponse(
        session_id=session_id,
        exam_id=exam_id,
        pdf_url=pdf_url,
        dashboard_url=dashboard_url,
        next_steps=next_steps,
        estimated_time_minutes=estimated_time_minutes,
    )


@router.get(
    "/status",
    summary="Wizard onboarding status",
    description="Check if tutor has completed first exam (for progress tracking)",
)
async def wizard_status(
    payload=Depends(require_scopes("exam:read")),
) -> dict[str, Any]:
    """
    Return onboarding completion status.
    
    V1: Simple check - has user created any exam sessions?
    V2: More sophisticated progress tracking (% complete, bottlenecks)
    """
    # TODO: Query exam_sessions table for count where user_id = payload.get("sub")
    # For V1, return mock data structure (user_id, org_id available from payload)
    
    return {
        "completed": False,  # Mock: False until first exam created
        "current_step": "quick_start",  # quick_start, exam_setup, review, done
        "progress_percent": 0,
        "first_exam_session_id": None,
        "ttfp_minutes": None,  # Time to first PDF (calculated when first PDF downloaded)
        "suggestions": [
            "Start with the Quick Start wizard to create your first exam",
            "Choose Math, Grade 10, Medium difficulty for best results",
        ],
    }
