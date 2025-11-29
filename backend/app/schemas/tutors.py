# backend/app/schemas/tutors.py
"""
튜터(가정교사) 관련 Pydantic 스키마
- TutorSessionSummary: 세션 목록용 요약 데이터
- TutorSessionDetail: 세션 상세 데이터 (Notes, Tasks 포함)
"""

from typing import List, Literal, Optional
from pydantic import BaseModel, Field

SessionStatus = Literal["Completed", "Upcoming"]


class TutorSessionSummary(BaseModel):
    """
    세션 목록용 요약 데이터
    
    사용처:
    - GET /api/tutors/{tutor_id}/sessions (목록)
    """
    id: str
    date: str = Field(
        ...,
        description="세션 날짜 (ISO8601 or YYYY-MM-DD)",
        json_schema_extra={"example": "2025-11-10"},
    )
    student_id: str
    student_name: str = Field(
        ...,
        json_schema_extra={"example": "홍길동"},
    )
    subject: str = Field(
        ...,
        description="과목",
        json_schema_extra={"example": "수학"},
    )
    topic: str = Field(
        ...,
        description="주제",
        json_schema_extra={"example": "미분·적분"},
    )
    status: SessionStatus

    class Config:
        from_attributes = True


class TutorSessionTask(BaseModel):
    """
    세션 내 할 일 (Task/Checklist)
    
    프론트엔드에서 체크리스트로 표시
    """
    label: str = Field(
        ...,
        description="할 일 설명",
        json_schema_extra={"example": "교과서 예제 5개 풀이"},
    )
    done: bool = Field(..., description="완료 여부")


class TutorSessionDetail(TutorSessionSummary):
    """
    세션 상세 데이터
    
    사용처:
    - GET /api/tutors/{tutor_id}/sessions/{session_id}
    
    포함 정보:
    - TutorSessionSummary의 모든 필드
    - duration_minutes: 세션 시간
    - notes: 세션 노트
    - tasks: 할 일 목록
    """
    duration_minutes: Optional[int] = Field(
        None,
        description="세션 지속 시간 (분)",
        ge=0,
        json_schema_extra={"example": 90},
    )
    notes: str = Field(
        ...,
        description="세션 노트/메모",
        json_schema_extra={
            "example": "개념 이해는 양호, 문제 풀이 속도를 조금 더 올릴 필요 있음.",
        },
    )
    tasks: List[TutorSessionTask] = Field(
        default_factory=list,
        description="세션 할 일 목록",
        json_schema_extra={
            "example": [
                {"label": "교과서 예제 5개 풀이", "done": True},
                {"label": "심화 문제 3개 풀이", "done": True},
                {"label": "개념 요약 정리 복습", "done": False},
            ]
        },
    )
