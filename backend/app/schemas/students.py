# backend/app/schemas/students.py
"""
학생 관련 Pydantic 스키마
- StudentSummary: 학생 목록용 요약 데이터
- StudentDetail: 학생 상세 데이터 (Ability Trend, Recent Tests 포함)
- ChildDetail: 학부모용 자녀 상세 데이터
"""

from typing import List, Literal, Optional
from pydantic import BaseModel, Field

StudentStatus = Literal["On Track", "At Risk", "Struggling"]


class StudentSummary(BaseModel):
    """
    학생 목록용 요약 데이터
    
    사용처:
    - GET /api/teachers/{teacher_id}/students (목록)
    """
    id: str
    name: str
    class_id: Optional[str] = None
    class_name: Optional[str] = None
    current_ability_theta: Optional[float] = Field(
        None, 
        description="IRT θ (ability parameter)",
        example=0.12
    )
    recent_score: Optional[float] = Field(
        None, 
        ge=0, 
        le=100, 
        description="최근 평균 점수 (%)",
        example=87.0
    )
    status: StudentStatus = "On Track"
    risk_flags: Optional[List[str]] = Field(
        default_factory=list, 
        description="위험 신호 목록",
        example=["최근 결석 없음", "추세 안정적"]
    )

    class Config:
        from_attributes = True


class AbilityPoint(BaseModel):
    """
    Ability Trend 차트 포인트
    
    프론트엔드에서 SVG 라인 차트 렌더링에 사용
    """
    label: str = Field(..., example="4w ago", description="시간 라벨")
    value: float = Field(..., description="θ 값", example=-0.2)


class RecentTest(BaseModel):
    """
    최근 시험 기록
    
    프론트엔드 StudentDetail 페이지에서 테이블로 표시
    """
    date: str = Field(..., description="시험 날짜 (ISO8601 or YYYY-MM-DD)", example="2025-11-10")
    name: str = Field(..., example="미분·적분 퀴즈")
    score: float = Field(..., ge=0, le=100, description="점수 (%)", example=90.0)


class StudentDetail(StudentSummary):
    """
    학생 상세 데이터
    
    사용처:
    - GET /api/teachers/{teacher_id}/students/{student_id}
    
    포함 정보:
    - StudentSummary의 모든 필드
    - ability_trend: 최근 5주 θ 추이
    - recent_tests: 최근 3개 시험 결과
    """
    ability_trend: List[AbilityPoint] = Field(
        default_factory=list,
        description="최근 5주 Ability θ 추이",
        example=[
            {"label": "4w ago", "value": -0.2},
            {"label": "3w ago", "value": -0.05},
            {"label": "2w ago", "value": 0.0},
            {"label": "1w ago", "value": 0.08},
            {"label": "now", "value": 0.12}
        ]
    )
    recent_tests: List[RecentTest] = Field(
        default_factory=list,
        description="최근 시험 결과 (최대 3개)"
    )


class ChildDetail(StudentDetail):
    """
    학부모용 자녀 상세 데이터
    
    사용처:
    - GET /api/parents/{parent_id}/children/{child_id}
    
    StudentDetail + 학부모 전용 필드:
    - study_time_month: 이번 달 학습 시간
    - strengths: 강점 영역
    - areas_to_improve: 개선 필요 영역
    - recent_activity: 최근 활동 로그
    """
    study_time_month: Optional[str] = Field(
        None, 
        example="12h / month",
        description="이번 달 총 학습 시간"
    )
    strengths: Optional[List[str]] = Field(
        default=None,
        description="학생의 강점 영역 (예: 도형, 함수 응용, 논리적 사고력)"
    )
    areas_to_improve: Optional[List[str]] = Field(
        default=None,
        alias="areasToImprove",  # Frontend 호환성
        description="개선이 필요한 영역 (예: 확률, 통계)"
    )
    recent_activity: Optional[List[dict]] = Field(
        default=None,
        alias="recentActivity",  # Frontend 호환성
        description="최근 활동 로그 [{'date': 'YYYY-MM-DD', 'description': '...'}]"
    )
