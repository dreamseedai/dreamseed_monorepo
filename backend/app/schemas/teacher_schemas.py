"""
Teacher portal schemas - Class management and student reports
"""
from __future__ import annotations

import uuid
from typing import List, Optional

from pydantic import BaseModel, Field


class TeacherClassStudent(BaseModel):
    """Single student in teacher's class list"""
    student_id: uuid.UUID = Field(..., alias="studentId")
    student_name: str = Field(..., alias="studentName")
    school: Optional[str] = None
    grade: Optional[str] = None
    label: Optional[str] = None  # 반/클래스 이름
    subject: str
    theta: float
    theta_se: float = Field(..., alias="thetaSe")
    theta_band: str = Field(..., alias="thetaBand")
    risk_level: str = Field(..., alias="riskLevel")
    delta_theta_14d: Optional[float] = Field(None, alias="deltaTheta14d")
    
    class Config:
        populate_by_name = True


class TeacherClassListResponse(BaseModel):
    """Response for GET /api/teacher/class-list"""
    teacher_id: uuid.UUID = Field(..., alias="teacherId")
    organization_id: uuid.UUID = Field(..., alias="organizationId")
    subject: str
    klass: Optional[str] = None
    window_days: int = Field(..., alias="windowDays")
    students: List[TeacherClassStudent]
    
    class Config:
        populate_by_name = True
