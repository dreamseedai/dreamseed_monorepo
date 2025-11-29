"""
FastAPI router for core entity CRUD operations

Provides REST endpoints for:
- Organizations
- Teachers
- Student-Classroom enrollments
- Exam Sessions
- Attempts

These endpoints follow RESTful conventions and include:
- CRUD operations
- Batch operations
- Statistics endpoints
- Proper error handling
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func, and_, desc
from sqlalchemy.orm import Session, selectinload
from sqlalchemy.exc import IntegrityError

from app.core.database import get_db
from app.models.core_entities import (
    Organization,
    Teacher,
    StudentClassroom,
    ExamSession,
    Attempt,
)
from app.models.student import Student
from app.models.student import Class
from app.schemas.core_schemas import (
    OrganizationCreate,
    OrganizationUpdate,
    OrganizationResponse,
    TeacherCreate,
    TeacherUpdate,
    TeacherResponse,
    StudentClassroomCreate,
    StudentClassroomResponse,
    ExamSessionCreate,
    ExamSessionUpdate,
    ExamSessionResponse,
    ExamSessionWithAttempts,
    AttemptCreate,
    AttemptUpdate,
    AttemptResponse,
    BulkEnrollmentRequest,
    BulkEnrollmentResponse,
    StudentExamStats,
    ClassExamStats,
)

router = APIRouter(prefix="/api/core", tags=["core"])


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Organizations
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@router.post("/organizations", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED)
def create_organization(org: OrganizationCreate, db: Session = Depends(get_db)):
    """Create a new organization"""
    db_org = Organization(**org.model_dump())
    db.add(db_org)
    db.commit()
    db.refresh(db_org)
    return db_org


@router.get("/organizations", response_model=List[OrganizationResponse])
def list_organizations(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    org_type: Optional[str] = Query(None, description="Filter by organization type"),
    db: Session = Depends(get_db),
):
    """List all organizations with optional filtering"""
    query = select(Organization)
    if org_type:
        query = query.where(Organization.type == org_type)
    query = query.offset(skip).limit(limit).order_by(Organization.id)
    
    result = db.execute(query)
    return result.scalars().all()


@router.get("/organizations/{org_id}", response_model=OrganizationResponse)
def get_organization(org_id: int, db: Session = Depends(get_db)):
    """Get a specific organization by ID"""
    org = db.get(Organization, org_id)
    if not org:
        raise HTTPException(status_code=404, detail=f"Organization {org_id} not found")
    return org


@router.patch("/organizations/{org_id}", response_model=OrganizationResponse)
def update_organization(org_id: int, org_update: OrganizationUpdate, db: Session = Depends(get_db)):
    """Update an organization"""
    org = db.get(Organization, org_id)
    if not org:
        raise HTTPException(status_code=404, detail=f"Organization {org_id} not found")
    
    update_data = org_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(org, key, value)
    
    db.commit()
    db.refresh(org)
    return org


@router.delete("/organizations/{org_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_organization(org_id: int, db: Session = Depends(get_db)):
    """Delete an organization"""
    org = db.get(Organization, org_id)
    if not org:
        raise HTTPException(status_code=404, detail=f"Organization {org_id} not found")
    
    db.delete(org)
    db.commit()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Teachers
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@router.post("/teachers", response_model=TeacherResponse, status_code=status.HTTP_201_CREATED)
def create_teacher(teacher: TeacherCreate, db: Session = Depends(get_db)):
    """Create a new teacher profile"""
    try:
        db_teacher = Teacher(**teacher.model_dump())
        db.add(db_teacher)
        db.commit()
        db.refresh(db_teacher)
        return db_teacher
    except IntegrityError as e:
        db.rollback()
        if "unique" in str(e).lower():
            raise HTTPException(status_code=400, detail="Teacher profile already exists for this user")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/teachers", response_model=List[TeacherResponse])
def list_teachers(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    org_id: Optional[int] = Query(None, description="Filter by organization"),
    subject: Optional[str] = Query(None, description="Filter by subject"),
    db: Session = Depends(get_db),
):
    """List all teachers with optional filtering"""
    query = select(Teacher)
    if org_id is not None:
        query = query.where(Teacher.org_id == org_id)
    if subject:
        query = query.where(Teacher.subject == subject)
    query = query.offset(skip).limit(limit).order_by(Teacher.id)
    
    result = db.execute(query)
    return result.scalars().all()


@router.get("/teachers/{teacher_id}", response_model=TeacherResponse)
def get_teacher(teacher_id: int, db: Session = Depends(get_db)):
    """Get a specific teacher by ID"""
    teacher = db.get(Teacher, teacher_id)
    if not teacher:
        raise HTTPException(status_code=404, detail=f"Teacher {teacher_id} not found")
    return teacher


@router.patch("/teachers/{teacher_id}", response_model=TeacherResponse)
def update_teacher(teacher_id: int, teacher_update: TeacherUpdate, db: Session = Depends(get_db)):
    """Update a teacher profile"""
    teacher = db.get(Teacher, teacher_id)
    if not teacher:
        raise HTTPException(status_code=404, detail=f"Teacher {teacher_id} not found")
    
    update_data = teacher_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(teacher, key, value)
    
    db.commit()
    db.refresh(teacher)
    return teacher


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Student-Classroom Enrollments
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@router.post("/enrollments", response_model=StudentClassroomResponse, status_code=status.HTTP_201_CREATED)
def enroll_student(enrollment: StudentClassroomCreate, db: Session = Depends(get_db)):
    """Enroll a student in a class"""
    # Verify student and class exist
    student = db.get(Student, enrollment.student_id)
    if not student:
        raise HTTPException(status_code=404, detail=f"Student {enrollment.student_id} not found")
    
    clazz = db.get(Class, enrollment.class_id)
    if not clazz:
        raise HTTPException(status_code=404, detail=f"Class {enrollment.class_id} not found")
    
    try:
        db_enrollment = StudentClassroom(**enrollment.model_dump())
        db.add(db_enrollment)
        db.commit()
        db.refresh(db_enrollment)
        return db_enrollment
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Student already enrolled in this class")


@router.post("/enrollments/bulk", response_model=BulkEnrollmentResponse)
def bulk_enroll_students(request: BulkEnrollmentRequest, db: Session = Depends(get_db)):
    """Enroll multiple students in a class"""
    # Verify class exists
    clazz = db.get(Class, request.class_id)
    if not clazz:
        raise HTTPException(status_code=404, detail=f"Class {request.class_id} not found")
    
    success_count = 0
    failed_student_ids = []
    
    for student_id in request.student_ids:
        try:
            enrollment = StudentClassroom(student_id=student_id, class_id=request.class_id)
            db.add(enrollment)
            db.commit()
            success_count += 1
        except IntegrityError:
            db.rollback()
            failed_student_ids.append(student_id)
    
    return BulkEnrollmentResponse(
        success_count=success_count,
        failed_count=len(failed_student_ids),
        failed_student_ids=failed_student_ids,
    )


@router.get("/classes/{class_id}/students", response_model=List[int])
def list_class_students(class_id: int, db: Session = Depends(get_db)):
    """Get all student IDs enrolled in a class"""
    query = select(StudentClassroom.student_id).where(StudentClassroom.class_id == class_id)
    result = db.execute(query)
    return result.scalars().all()


@router.delete("/enrollments/{student_id}/{class_id}", status_code=status.HTTP_204_NO_CONTENT)
def unenroll_student(student_id: int, class_id: int, db: Session = Depends(get_db)):
    """Remove a student from a class"""
    query = select(StudentClassroom).where(
        and_(StudentClassroom.student_id == student_id, StudentClassroom.class_id == class_id)
    )
    enrollment = db.execute(query).scalar_one_or_none()
    
    if not enrollment:
        raise HTTPException(status_code=404, detail="Enrollment not found")
    
    db.delete(enrollment)
    db.commit()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Exam Sessions
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@router.post("/exam-sessions", response_model=ExamSessionResponse, status_code=status.HTTP_201_CREATED)
def create_exam_session(exam: ExamSessionCreate, db: Session = Depends(get_db)):
    """Start a new exam session"""
    # Verify student exists
    student = db.get(Student, exam.student_id)
    if not student:
        raise HTTPException(status_code=404, detail=f"Student {exam.student_id} not found")
    
    db_exam = ExamSession(**exam.model_dump())
    db.add(db_exam)
    db.commit()
    db.refresh(db_exam)
    return db_exam


@router.get("/exam-sessions", response_model=List[ExamSessionResponse])
def list_exam_sessions(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    student_id: Optional[int] = Query(None, description="Filter by student"),
    class_id: Optional[int] = Query(None, description="Filter by class"),
    exam_type: Optional[str] = Query(None, description="Filter by exam type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    db: Session = Depends(get_db),
):
    """List exam sessions with optional filtering"""
    query = select(ExamSession)
    
    if student_id is not None:
        query = query.where(ExamSession.student_id == student_id)
    if class_id is not None:
        query = query.where(ExamSession.class_id == class_id)
    if exam_type:
        query = query.where(ExamSession.exam_type == exam_type)
    if status:
        query = query.where(ExamSession.status == status)
    
    query = query.offset(skip).limit(limit).order_by(desc(ExamSession.started_at))
    
    result = db.execute(query)
    return result.scalars().all()


@router.get("/exam-sessions/{session_id}", response_model=ExamSessionWithAttempts)
def get_exam_session(session_id: int, db: Session = Depends(get_db)):
    """Get a specific exam session with attempts"""
    query = select(ExamSession).where(ExamSession.id == session_id).options(selectinload(ExamSession.attempts))
    exam = db.execute(query).scalar_one_or_none()
    
    if not exam:
        raise HTTPException(status_code=404, detail=f"Exam session {session_id} not found")
    return exam


@router.patch("/exam-sessions/{session_id}", response_model=ExamSessionResponse)
def update_exam_session(session_id: int, exam_update: ExamSessionUpdate, db: Session = Depends(get_db)):
    """Update an exam session (typically for completion)"""
    exam = db.get(ExamSession, session_id)
    if not exam:
        raise HTTPException(status_code=404, detail=f"Exam session {session_id} not found")
    
    update_data = exam_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(exam, key, value)
    
    db.commit()
    db.refresh(exam)
    return exam


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Attempts
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@router.post("/attempts", response_model=AttemptResponse, status_code=status.HTTP_201_CREATED)
def create_attempt(attempt: AttemptCreate, db: Session = Depends(get_db)):
    """Record a student's attempt on an item"""
    # Verify exam session exists
    exam = db.get(ExamSession, attempt.exam_session_id)
    if not exam:
        raise HTTPException(status_code=404, detail=f"Exam session {attempt.exam_session_id} not found")
    
    db_attempt = Attempt(**attempt.model_dump())
    db.add(db_attempt)
    db.commit()
    db.refresh(db_attempt)
    return db_attempt


@router.get("/exam-sessions/{session_id}/attempts", response_model=List[AttemptResponse])
def list_session_attempts(session_id: int, db: Session = Depends(get_db)):
    """Get all attempts for an exam session"""
    query = select(Attempt).where(Attempt.exam_session_id == session_id).order_by(Attempt.created_at)
    result = db.execute(query)
    return result.scalars().all()


@router.patch("/attempts/{attempt_id}", response_model=AttemptResponse)
def update_attempt(attempt_id: int, attempt_update: AttemptUpdate, db: Session = Depends(get_db)):
    """Update an attempt (e.g., for scoring open-ended questions)"""
    attempt = db.get(Attempt, attempt_id)
    if not attempt:
        raise HTTPException(status_code=404, detail=f"Attempt {attempt_id} not found")
    
    update_data = attempt_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(attempt, key, value)
    
    db.commit()
    db.refresh(attempt)
    return attempt


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Statistics & Analytics
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@router.get("/students/{student_id}/exam-stats", response_model=StudentExamStats)
def get_student_exam_stats(student_id: int, db: Session = Depends(get_db)):
    """Get exam statistics for a student"""
    # Verify student exists
    student = db.get(Student, student_id)
    if not student:
        raise HTTPException(status_code=404, detail=f"Student {student_id} not found")
    
    # Calculate statistics
    query = select(
        func.count(ExamSession.id).label("total_exams"),
        func.count(ExamSession.id).filter(ExamSession.status == "completed").label("completed_exams"),
        func.avg(ExamSession.score).filter(ExamSession.status == "completed").label("average_score"),
        func.avg(ExamSession.theta).filter(ExamSession.status == "completed").label("average_theta"),
        func.max(ExamSession.started_at).label("latest_exam_date"),
    ).where(ExamSession.student_id == student_id)
    
    result = db.execute(query).one()
    
    return StudentExamStats(
        student_id=student_id,
        total_exams=result.total_exams or 0,
        completed_exams=result.completed_exams or 0,
        average_score=result.average_score,
        average_theta=result.average_theta,
        latest_exam_date=result.latest_exam_date,
    )


@router.get("/classes/{class_id}/exam-stats", response_model=ClassExamStats)
def get_class_exam_stats(class_id: int, db: Session = Depends(get_db)):
    """Get exam statistics for a class"""
    # Verify class exists
    clazz = db.get(Class, class_id)
    if not clazz:
        raise HTTPException(status_code=404, detail=f"Class {class_id} not found")
    
    # Get student count
    student_count = db.execute(
        select(func.count(StudentClassroom.student_id)).where(StudentClassroom.class_id == class_id)
    ).scalar_one()
    
    # Calculate exam statistics
    query = select(
        func.count(ExamSession.id).label("total_exams"),
        func.avg(ExamSession.score).filter(ExamSession.status == "completed").label("average_score"),
        func.avg(ExamSession.theta).filter(ExamSession.status == "completed").label("average_theta"),
        func.stddev(ExamSession.score).filter(ExamSession.status == "completed").label("score_std_dev"),
    ).where(ExamSession.class_id == class_id)
    
    result = db.execute(query).one()
    
    return ClassExamStats(
        class_id=class_id,
        total_students=student_count,
        total_exams=result.total_exams or 0,
        average_score=result.average_score,
        average_theta=result.average_theta,
        score_std_dev=result.score_std_dev,
    )
