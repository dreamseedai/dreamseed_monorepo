"""
Pydantic schemas for core entities (INTEGER-based)

These schemas define the request/response models for FastAPI endpoints.
They provide validation, serialization, and API documentation.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from decimal import Decimal

from pydantic import BaseModel, Field, EmailStr, ConfigDict


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Users
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class UserBase(BaseModel):
    """Base schema for User"""
    email: EmailStr = Field(..., description="User email address")
    username: Optional[str] = Field(None, max_length=255, description="Username")
    role: str = Field(..., max_length=20, description="User role: student, teacher, parent, admin, super_admin")


class UserCreate(UserBase):
    """Schema for creating a new user"""
    password: str = Field(..., min_length=8, description="User password (will be hashed)")
    org_id: Optional[int] = Field(None, description="Organization ID")


class UserUpdate(BaseModel):
    """Schema for updating a user"""
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, max_length=255)
    role: Optional[str] = Field(None, max_length=20)
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    """Schema for user response (without password)"""
    id: int
    org_id: Optional[int]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Students
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class StudentBase(BaseModel):
    """Base schema for Student"""
    user_id: int = Field(..., description="Reference to users.id")
    grade: Optional[str] = Field(None, max_length=20, description="Grade level")
    birth_year: Optional[int] = Field(None, ge=1900, le=2100, description="Birth year")
    locale: Optional[str] = Field(None, max_length=20, description="Preferred locale (e.g., ko-KR, en-US)")


class StudentCreate(StudentBase):
    """Schema for creating a new student"""
    org_id: Optional[int] = Field(None, description="Organization ID")


class StudentUpdate(BaseModel):
    """Schema for updating a student"""
    grade: Optional[str] = Field(None, max_length=20)
    birth_year: Optional[int] = Field(None, ge=1900, le=2100)
    locale: Optional[str] = Field(None, max_length=20)
    org_id: Optional[int] = None


class StudentResponse(StudentBase):
    """Schema for student response"""
    id: int
    org_id: Optional[int]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Classes
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class ClassBase(BaseModel):
    """Base schema for Class"""
    name: str = Field(..., max_length=255, description="Class name")
    grade: Optional[str] = Field(None, max_length=20, description="Grade level")
    subject: Optional[str] = Field(None, max_length=100, description="Subject taught")


class ClassCreate(ClassBase):
    """Schema for creating a new class"""
    org_id: Optional[int] = Field(None, description="Organization ID")
    teacher_id: Optional[int] = Field(None, description="Teacher ID")


class ClassUpdate(BaseModel):
    """Schema for updating a class"""
    name: Optional[str] = Field(None, max_length=255)
    grade: Optional[str] = Field(None, max_length=20)
    subject: Optional[str] = Field(None, max_length=100)
    teacher_id: Optional[int] = None


class ClassResponse(ClassBase):
    """Schema for class response"""
    id: int
    org_id: Optional[int]
    teacher_id: Optional[int]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Organizations
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class OrganizationBase(BaseModel):
    """Base schema for Organization"""
    name: str = Field(..., max_length=255, description="Organization name")
    type: Optional[str] = Field(None, max_length=50, description="Organization type (school, academy, tutoring_center)")


class OrganizationCreate(OrganizationBase):
    """Schema for creating a new organization"""
    pass


class OrganizationUpdate(BaseModel):
    """Schema for updating an organization"""
    name: Optional[str] = Field(None, max_length=255)
    type: Optional[str] = Field(None, max_length=50)


class OrganizationResponse(OrganizationBase):
    """Schema for organization response"""
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Teachers
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TeacherBase(BaseModel):
    """Base schema for Teacher"""
    user_id: int = Field(..., description="Reference to users.id")
    org_id: Optional[int] = Field(None, description="Organization ID")
    subject: Optional[str] = Field(None, max_length=100, description="Primary subject taught")
    meta: Optional[Dict[str, Any]] = Field(None, description="Additional metadata (certifications, bio, etc.)")


class TeacherCreate(TeacherBase):
    """Schema for creating a new teacher profile"""
    pass


class TeacherUpdate(BaseModel):
    """Schema for updating a teacher profile"""
    org_id: Optional[int] = None
    subject: Optional[str] = Field(None, max_length=100)
    meta: Optional[Dict[str, Any]] = None


class TeacherResponse(TeacherBase):
    """Schema for teacher response"""
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Student-Classroom Enrollment
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class StudentClassroomBase(BaseModel):
    """Base schema for student-classroom enrollment"""
    student_id: int
    class_id: int


class StudentClassroomCreate(StudentClassroomBase):
    """Schema for enrolling a student in a class"""
    pass


class StudentClassroomResponse(StudentClassroomBase):
    """Schema for student-classroom enrollment response"""
    enrolled_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Exam Sessions
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class ExamSessionBase(BaseModel):
    """Base schema for ExamSession"""
    student_id: int = Field(..., description="Student taking the exam")
    class_id: Optional[int] = Field(None, description="Class context (if applicable)")
    exam_type: str = Field(..., max_length=50, description="Exam type: placement, practice, mock, official, quiz")
    meta: Optional[Dict[str, Any]] = Field(None, description="Algorithm config, stopping rules, etc.")


class ExamSessionCreate(BaseModel):
    """
    Schema for starting a new exam session.
    
    Used by students to initiate an exam. The student_id will be
    extracted from the authenticated user context.
    """
    exam_type: str = Field(..., max_length=50, description="Exam type: placement, practice, mock, official, quiz")
    class_id: Optional[int] = Field(None, description="Class context (if applicable)")
    meta: Optional[Dict[str, Any]] = Field(None, description="Algorithm config, stopping rules, etc.")


class ExamSessionUpdate(BaseModel):
    """Schema for updating an exam session (typically for completion)"""
    status: Optional[str] = Field(None, max_length=20, description="Status: in_progress, completed, abandoned")
    ended_at: Optional[datetime] = None
    score: Optional[Decimal] = Field(None, ge=0, le=100, description="Final score (0-100)")
    duration_sec: Optional[int] = Field(None, ge=0, description="Total duration in seconds")
    theta: Optional[Decimal] = Field(None, description="IRT ability estimate")
    standard_error: Optional[Decimal] = Field(None, ge=0, description="Standard error of theta")
    meta: Optional[Dict[str, Any]] = None


class ExamSessionResponse(ExamSessionBase):
    """Schema for exam session response"""
    id: int
    status: str
    started_at: datetime
    ended_at: Optional[datetime]
    score: Optional[Decimal]
    duration_sec: Optional[int]
    theta: Optional[Decimal]
    standard_error: Optional[Decimal]

    model_config = ConfigDict(from_attributes=True)


class ExamSessionWithAttempts(ExamSessionResponse):
    """Extended exam session response including attempts"""
    attempts: List["AttemptResponse"] = []

    model_config = ConfigDict(from_attributes=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Attempts
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class AttemptBase(BaseModel):
    """Base schema for Attempt"""
    student_id: int
    exam_session_id: int
    item_id: Optional[int] = Field(None, description="Reference to item/question")
    correct: bool = Field(..., description="Whether the answer was correct")
    submitted_answer: Optional[str] = Field(None, description="Text answer for open-ended questions")
    selected_choice: Optional[int] = Field(None, ge=1, le=10, description="Selected choice number for multiple-choice")
    response_time_ms: Optional[int] = Field(None, ge=0, description="Response time in milliseconds")
    meta: Optional[Dict[str, Any]] = Field(None, description="Item parameters, partial credit, etc.")


class AnswerSubmit(BaseModel):
    """
    Schema for submitting an answer during an exam.
    
    Used by students to record their response to an item.
    The exam_session_id and student verification will be handled
    by the endpoint logic.
    """
    exam_session_id: int = Field(..., description="Current exam session ID")
    item_id: int = Field(..., description="Item/question being answered")
    answer: Optional[str] = Field(None, description="Text answer for open-ended questions")
    selected_choice: Optional[int] = Field(None, ge=1, le=10, description="Selected choice for multiple-choice")
    response_time_ms: Optional[int] = Field(None, ge=0, description="Time taken to answer in milliseconds")
    correct: bool = Field(..., description="Whether the answer is correct (v0.5: client-side scoring)")


class AttemptCreate(AttemptBase):
    """Schema for creating a new attempt (internal use)"""
    pass


class AttemptUpdate(BaseModel):
    """Schema for updating an attempt (e.g., scoring open-ended questions)"""
    correct: Optional[bool] = None
    meta: Optional[Dict[str, Any]] = None


class AttemptResponse(AttemptBase):
    """Schema for attempt response"""
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Batch Operations
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class BulkEnrollmentRequest(BaseModel):
    """Schema for bulk enrolling students in a class"""
    class_id: int
    student_ids: List[int] = Field(..., min_length=1, max_length=1000)


class BulkEnrollmentResponse(BaseModel):
    """Response for bulk enrollment"""
    success_count: int
    failed_count: int
    failed_student_ids: List[int] = []


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Statistics & Analytics
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class StudentExamStats(BaseModel):
    """Statistics for a student's exam performance"""
    student_id: int
    total_exams: int
    completed_exams: int
    average_score: Optional[Decimal]
    average_theta: Optional[Decimal]
    latest_exam_date: Optional[datetime]


class ClassExamStats(BaseModel):
    """Statistics for a class's exam performance"""
    class_id: int
    total_students: int
    total_exams: int
    average_score: Optional[Decimal]
    average_theta: Optional[Decimal]
    score_std_dev: Optional[Decimal]


# Forward references for nested models
ExamSessionWithAttempts.model_rebuild()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Simplified Aliases (for backward compatibility)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Aliases for simpler naming convention
UserOut = UserResponse
StudentOut = StudentResponse
ClassOut = ClassResponse
ExamSessionOut = ExamSessionResponse
AttemptOut = AttemptResponse
