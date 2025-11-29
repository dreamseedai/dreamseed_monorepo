"""
Assignment API Router - REST endpoints for homework management.
"""

from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status as status_lib, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.core.database import get_async_session
from app.models.user import User
from app.services.assignments import (
    AssignmentService,
    AssignmentType,
    AssignmentStatus,
    SubmissionStatus,
    get_assignment_service,
)

router = APIRouter(prefix="/assignments", tags=["assignments"])


# ============================================================================
# Pydantic Schemas
# ============================================================================


class AssignmentCreate(BaseModel):
    """Schema for creating an assignment"""

    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    assignment_type: AssignmentType
    student_ids: List[int] = Field(..., min_length=1)
    class_id: Optional[str] = None
    subject: Optional[str] = None
    grade: Optional[str] = None
    template_id: Optional[str] = None
    total_points: Optional[int] = Field(None, ge=0)
    due_date: Optional[datetime] = None
    instructions: Optional[str] = None
    attachments: Optional[dict] = None
    metadata: Optional[dict] = None
    status: AssignmentStatus = AssignmentStatus.ACTIVE


class AssignmentUpdate(BaseModel):
    """Schema for updating an assignment"""

    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    total_points: Optional[int] = Field(None, ge=0)
    due_date: Optional[datetime] = None
    instructions: Optional[str] = None
    attachments: Optional[dict] = None
    metadata: Optional[dict] = None
    status: Optional[AssignmentStatus] = None


class AssignmentResponse(BaseModel):
    """Schema for assignment response"""

    id: int
    title: str
    description: Optional[str]
    teacher_id: int
    class_id: Optional[str]
    subject: Optional[str]
    grade: Optional[str]
    assignment_type: str
    template_id: Optional[str]
    total_points: Optional[int]
    due_date: Optional[datetime]
    assigned_date: datetime
    status: str
    instructions: Optional[str]
    attachments: Optional[dict]
    metadata: Optional[dict]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SubmissionCreate(BaseModel):
    """Schema for submitting an assignment"""

    submission_text: Optional[str] = None
    attachments: Optional[dict] = None
    metadata: Optional[dict] = None


class GradeSubmission(BaseModel):
    """Schema for grading a submission"""

    score: Optional[int] = Field(None, ge=0)
    grade: Optional[str] = Field(None, max_length=10)
    feedback: Optional[str] = None
    rubric_scores: Optional[dict] = None


class SubmissionResponse(BaseModel):
    """Schema for submission response"""

    id: int
    assignment_id: int
    student_id: int
    submission_text: Optional[str]
    attachments: Optional[dict]
    submitted_at: datetime
    is_late: bool
    status: str
    score: Optional[int]
    grade: Optional[str]
    feedback: Optional[str]
    graded_at: Optional[datetime]
    graded_by: Optional[int]
    rubric_scores: Optional[dict]
    metadata: Optional[dict]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AssignmentStatistics(BaseModel):
    """Schema for assignment statistics"""

    assignment_id: int
    total_students: int
    submitted_count: int
    graded_count: int
    late_count: int
    pending_count: int
    not_submitted_count: int
    avg_score: Optional[float]
    submission_rate: float
    grading_rate: float


# ============================================================================
# Dependency: Get current user (mock for now)
# ============================================================================


async def get_current_user():
    """
    TODO: Replace with actual authentication
    Mock user for development

    Returns a mock user object with id attribute.
    In production, this should validate JWT token and return actual User model.
    """

    # This should be replaced with actual JWT token validation
    # For now, return a simple object with id attribute
    class MockUser:
        def __init__(self):
            self.id = 1

    return MockUser()


# ============================================================================
# Assignment Endpoints (Teacher)
# ============================================================================


@router.post(
    "/", response_model=AssignmentResponse, status_code=status_lib.HTTP_201_CREATED
)
async def create_assignment(
    assignment: AssignmentCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
    service: AssignmentService = Depends(get_assignment_service),
):
    """
    Create a new assignment and assign it to students.

    Teacher only endpoint.
    """
    try:
        created_assignment = await service.create_assignment(
            db=db,
            title=assignment.title,
            teacher_id=int(user.id),  # type: ignore
            assignment_type=assignment.assignment_type,
            student_ids=assignment.student_ids,
            description=assignment.description,
            class_id=assignment.class_id,
            subject=assignment.subject,
            grade=assignment.grade,
            template_id=assignment.template_id,
            total_points=assignment.total_points,
            due_date=assignment.due_date,
            instructions=assignment.instructions,
            attachments=assignment.attachments,
            metadata=assignment.metadata,
            status=assignment.status,
        )
        return created_assignment
    except Exception as e:
        raise HTTPException(
            status_code=status_lib.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/teacher", response_model=List[AssignmentResponse])
async def get_teacher_assignments(
    class_id: Optional[str] = Query(None),
    status: Optional[AssignmentStatus] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
    service: AssignmentService = Depends(get_assignment_service),
):
    """
    Get all assignments created by the current teacher.

    Supports filtering by class_id and status.
    """
    assignments = await service.get_teacher_assignments(
        db=db,
        teacher_id=int(user.id),  # type: ignore
        class_id=class_id,
        status=status,
        limit=limit,
        offset=offset,
    )
    return assignments


@router.get("/{assignment_id}", response_model=AssignmentResponse)
async def get_assignment(
    assignment_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
    service: AssignmentService = Depends(get_assignment_service),
):
    """
    Get assignment details by ID.

    Teacher must own the assignment.
    """
    assignment = await service.get_assignment(
        db=db,
        assignment_id=assignment_id,
        teacher_id=int(user.id),  # type: ignore
    )

    if not assignment:
        raise HTTPException(
            status_code=status_lib.HTTP_404_NOT_FOUND,
            detail="Assignment not found",
        )

    return assignment


@router.put("/{assignment_id}", response_model=AssignmentResponse)
async def update_assignment(
    assignment_id: int,
    update_data: AssignmentUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
    service: AssignmentService = Depends(get_assignment_service),
):
    """
    Update an assignment.

    Teacher must own the assignment.
    """
    update_dict = update_data.dict(exclude_unset=True)

    assignment = await service.update_assignment(
        db=db,
        assignment_id=assignment_id,
        teacher_id=int(user.id),  # type: ignore
        **update_dict,
    )

    if not assignment:
        raise HTTPException(
            status_code=status_lib.HTTP_404_NOT_FOUND,
            detail="Assignment not found",
        )

    return assignment


@router.delete("/{assignment_id}", status_code=status_lib.HTTP_204_NO_CONTENT)
async def delete_assignment(
    assignment_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
    service: AssignmentService = Depends(get_assignment_service),
):
    """
    Delete an assignment.

    Teacher must own the assignment.
    """
    deleted = await service.delete_assignment(
        db=db,
        assignment_id=assignment_id,
        teacher_id=int(user.id),  # type: ignore
    )

    if not deleted:
        raise HTTPException(
            status_code=status_lib.HTTP_404_NOT_FOUND,
            detail="Assignment not found",
        )

    return None


@router.get("/{assignment_id}/statistics", response_model=AssignmentStatistics)
async def get_assignment_statistics(
    assignment_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
    service: AssignmentService = Depends(get_assignment_service),
):
    """
    Get statistics for an assignment.

    Shows submission rates, grading progress, average scores, etc.
    Teacher must own the assignment.
    """
    stats = await service.get_assignment_statistics(
        db=db,
        assignment_id=assignment_id,
        teacher_id=int(user.id),  # type: ignore
    )

    if not stats:
        raise HTTPException(
            status_code=status_lib.HTTP_404_NOT_FOUND,
            detail="Assignment not found",
        )

    return stats


@router.get("/{assignment_id}/submissions", response_model=List[SubmissionResponse])
async def get_assignment_submissions(
    assignment_id: int,
    status: Optional[SubmissionStatus] = Query(None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
    service: AssignmentService = Depends(get_assignment_service),
):
    """
    Get all submissions for an assignment.

    Teacher view to see all student submissions.
    Teacher must own the assignment.
    """
    submissions = await service.get_assignment_submissions(
        db=db,
        assignment_id=assignment_id,
        teacher_id=int(user.id),  # type: ignore
        status=status,
    )

    return submissions


# ============================================================================
# Submission Endpoints (Student)
# ============================================================================


@router.get("/student/my-assignments", response_model=List[AssignmentResponse])
async def get_my_assignments(
    status: Optional[AssignmentStatus] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
    service: AssignmentService = Depends(get_assignment_service),
):
    """
    Get assignments assigned to the current student.

    Student endpoint.
    """
    assignments = await service.get_student_assignments(
        db=db,
        student_id=int(user.id),  # type: ignore
        status=status,
        limit=limit,
        offset=offset,
    )
    return assignments


@router.post(
    "/{assignment_id}/submit",
    response_model=SubmissionResponse,
    status_code=status_lib.HTTP_201_CREATED,
)
async def submit_assignment(
    assignment_id: int,
    submission: SubmissionCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
    service: AssignmentService = Depends(get_assignment_service),
):
    """
    Submit an assignment.

    Student endpoint. Creates new submission or updates existing one.
    """
    try:
        created_submission = await service.submit_assignment(
            db=db,
            assignment_id=assignment_id,
            student_id=int(user.id),  # type: ignore
            submission_text=submission.submission_text,
            attachments=submission.attachments,
            metadata=submission.metadata,
        )
        return created_submission
    except ValueError as e:
        raise HTTPException(
            status_code=status_lib.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status_lib.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/{assignment_id}/my-submission", response_model=SubmissionResponse)
async def get_my_submission(
    assignment_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
    service: AssignmentService = Depends(get_assignment_service),
):
    """
    Get the current student's submission for an assignment.

    Student endpoint.
    """
    submission = await service.get_student_submission(
        db=db,
        assignment_id=assignment_id,
        student_id=int(user.id),  # type: ignore
    )

    if not submission:
        raise HTTPException(
            status_code=status_lib.HTTP_404_NOT_FOUND,
            detail="Submission not found",
        )

    return submission


# ============================================================================
# Grading Endpoints (Teacher)
# ============================================================================


@router.post("/submissions/{submission_id}/grade", response_model=SubmissionResponse)
async def grade_submission(
    submission_id: int,
    grade_data: GradeSubmission,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
    service: AssignmentService = Depends(get_assignment_service),
):
    """
    Grade a student's submission.

    Teacher endpoint. Provides score, grade, feedback, and rubric scores.
    """
    graded_submission = await service.grade_submission(
        db=db,
        submission_id=submission_id,
        grader_id=int(user.id),  # type: ignore
        score=grade_data.score,
        grade=grade_data.grade,
        feedback=grade_data.feedback,
        rubric_scores=grade_data.rubric_scores,
    )

    if not graded_submission:
        raise HTTPException(
            status_code=status_lib.HTTP_404_NOT_FOUND,
            detail="Submission not found",
        )

    return graded_submission


@router.get("/submissions/{submission_id}", response_model=SubmissionResponse)
async def get_submission(
    submission_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Get submission by ID.

    Teacher can view any submission, student can view their own.
    """
    from sqlalchemy import select
    from app.models.assignment_models import Submission

    stmt = select(Submission).where(Submission.id == submission_id)
    result = await db.execute(stmt)
    submission = result.scalar_one_or_none()

    if not submission:
        raise HTTPException(
            status_code=status_lib.HTTP_404_NOT_FOUND,
            detail="Submission not found",
        )

    # TODO: Add permission check (teacher owns assignment OR student owns submission)

    return submission
