# Tutor Domain Implementation Guide

## 개요

Tutor 도메인은 DreamSeed CAT 시스템에 1:1 또는 소그룹 과외/튜터링 기능을 제공합니다.

### Teacher vs Tutor 비교

| 구분 | Teacher | Tutor |
|------|---------|-------|
| **소속** | 학교/학원 | 개인/플랫폼 |
| **관리 단위** | 반(Class) | 개별 학생 |
| **수업 형태** | 다수 학생 동시 | 1:1 또는 소그룹 |
| **관계** | 고정 (학기 단위) | 유동적 (계약 기반) |
| **평가** | 내부 평가 | 학생/학부모 평가 |

## 엔티티 구조

### 1. Tutor (튜터 프로필)

```python
from app.models import Tutor

tutor = Tutor(
    user_id=user_id,
    org_id=None,  # 개인 튜터
    subjects=['math', 'physics'],
    bio="10년 경력의 수학 전문 튜터입니다.",
    hourly_rate=50000,
    years_experience=10,
    education="서울대학교 수학교육과 졸업",
    certifications=['중등교사자격증', '수학교육박사'],
    available_hours={
        "mon": ["09:00-12:00", "14:00-18:00"],
        "wed": ["10:00-17:00"],
        "fri": ["09:00-12:00"]
    },
    is_active=True
)
db.add(tutor)
db.commit()
```

### 2. TutorSession (튜터링 세션)

```python
from app.models import TutorSession
from datetime import date, datetime

session = TutorSession(
    tutor_id=tutor_user_id,
    student_id=student_id,
    date=date(2025, 1, 15),
    subject="수학",
    topic="이차방정식",
    status="upcoming",  # 'upcoming', 'in_progress', 'completed', 'cancelled'
    duration_minutes=60,
    mode="online",  # 'online', 'offline', 'video', 'chat'
    notes="중간고사 대비 집중 학습"
)
db.add(session)
db.commit()

# 세션 시작
session.status = "in_progress"
session.started_at = datetime.utcnow()
db.commit()

# 세션 종료
session.status = "completed"
session.ended_at = datetime.utcnow()
session.session_rating = 5
session.session_feedback = "매우 만족스러운 수업이었습니다."
db.commit()
```

### 3. TutorNote (세션 피드백)

```python
from app.models import TutorNote

# 세션 요약
summary = TutorNote(
    tutor_session_id=session.id,
    author_id=tutor_user_id,
    note_type="summary",
    title="오늘 수업 요약",
    content="""
    - 이차방정식 근의 공식 학습
    - 판별식을 이용한 근의 개수 판정
    - 연습문제 10문제 풀이
    """,
    is_visible_to_student=True,
    is_visible_to_parent=True
)

# 과제
homework = TutorNote(
    tutor_session_id=session.id,
    author_id=tutor_user_id,
    note_type="homework",
    title="다음 수업 과제",
    content="교재 p.45-47 문제 1-20번 풀어오기",
    is_visible_to_student=True,
    is_visible_to_parent=True
)

# 학부모 메시지
parent_msg = TutorNote(
    tutor_session_id=session.id,
    author_id=tutor_user_id,
    note_type="parent_message",
    title="학부모님께",
    content="오늘 수업에서 이차방정식 개념을 잘 이해했습니다. 다음 주까지 복습하면 좋을 것 같습니다.",
    is_visible_to_student=False,
    is_visible_to_parent=True
)

# 진도 기록
progress = TutorNote(
    tutor_session_id=session.id,
    author_id=tutor_user_id,
    note_type="progress",
    title="진도 체크",
    content="중등 수학 2-1: 이차방정식 단원 60% 완료",
    is_visible_to_student=True,
    is_visible_to_parent=True
)

db.add_all([summary, homework, parent_msg, progress])
db.commit()
```

### 4. TutorStudentRelation (튜터-학생 관계)

```python
from app.models import TutorStudentRelation
from datetime import datetime
from decimal import Decimal

# 매칭 요청
relation = TutorStudentRelation(
    tutor_id=tutor.id,
    student_id=student_id,
    status="pending",  # 'pending', 'active', 'paused', 'ended'
    subjects=['math', 'physics'],
    weekly_hours=Decimal('3.0'),
    contract_type="monthly",  # 'monthly', 'per_session', 'package'
    rate_per_hour=Decimal('50000.00'),
    notes="중간고사 대비 집중 과외"
)
db.add(relation)
db.commit()

# 승인 (Approval 시스템과 연동 가능)
relation.status = "active"
relation.started_at = datetime.utcnow()
db.commit()

# 일시 중지
relation.status = "paused"
db.commit()

# 종료
relation.status = "ended"
relation.ended_at = datetime.utcnow()
db.commit()
```

### 5. TutorAvailability (가용 시간)

```python
from app.models import TutorAvailability
from datetime import time

# 월요일 오전
availability1 = TutorAvailability(
    tutor_id=tutor.id,
    day_of_week=0,  # 0=Monday, 6=Sunday
    start_time=time(9, 0),
    end_time=time(12, 0),
    is_available=True,
    notes="오전 시간대 선호"
)

# 수요일 오후
availability2 = TutorAvailability(
    tutor_id=tutor.id,
    day_of_week=2,  # Wednesday
    start_time=time(14, 0),
    end_time=time(18, 0),
    is_available=True
)

# 금요일 (불가능)
availability3 = TutorAvailability(
    tutor_id=tutor.id,
    day_of_week=4,  # Friday
    start_time=time(9, 0),
    end_time=time(17, 0),
    is_available=False,
    notes="개인 일정으로 불가"
)

db.add_all([availability1, availability2, availability3])
db.commit()
```

### 6. TutorRating (튜터 평가)

```python
from app.models import TutorRating

rating = TutorRating(
    tutor_id=tutor.id,
    student_id=student_id,
    session_id=session.id,
    rating=5,  # 1-5
    comment="매우 친절하고 이해하기 쉽게 설명해주셨습니다.",
    created_by=parent_user_id  # 학부모가 평가
)
db.add(rating)
db.commit()

# 튜터의 평균 평점은 자동 업데이트됨 (Trigger)
tutor = db.query(Tutor).get(tutor.id)
print(f"평균 평점: {tutor.rating_avg} ({tutor.rating_count}개 평가)")
```

## API 엔드포인트 예시

### 튜터 관리 API

```python
# backend/app/api/routers/tutors.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models import Tutor, TutorSession, TutorNote
from app.core.database import get_db

router = APIRouter(prefix="/api/tutors", tags=["tutors"])

@router.get("/")
def list_tutors(
    subject: str = None,
    min_rating: float = None,
    db: Session = Depends(get_db)
):
    """튜터 목록 조회"""
    query = db.query(Tutor).filter(Tutor.is_active == True)
    
    if subject:
        query = query.filter(Tutor.subjects.contains([subject]))
    
    if min_rating:
        query = query.filter(Tutor.rating_avg >= min_rating)
    
    tutors = query.order_by(Tutor.rating_avg.desc()).all()
    return {"tutors": tutors}

@router.get("/{tutor_id}")
def get_tutor(tutor_id: int, db: Session = Depends(get_db)):
    """튜터 프로필 상세"""
    tutor = db.query(Tutor).get(tutor_id)
    if not tutor:
        raise HTTPException(404, "Tutor not found")
    return tutor

@router.post("/{tutor_id}/sessions")
def create_session(
    tutor_id: int,
    session_data: dict,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """세션 예약"""
    session = TutorSession(
        tutor_id=tutor_id,
        student_id=session_data["student_id"],
        date=session_data["date"],
        subject=session_data["subject"],
        duration_minutes=session_data["duration_minutes"]
    )
    db.add(session)
    db.commit()
    return {"session_id": session.id}

@router.get("/{tutor_id}/sessions")
def list_sessions(
    tutor_id: int,
    status: str = None,
    db: Session = Depends(get_db)
):
    """튜터 세션 목록"""
    query = db.query(TutorSession).filter(
        TutorSession.tutor_id == tutor_id
    )
    
    if status:
        query = query.filter(TutorSession.status == status)
    
    sessions = query.order_by(TutorSession.date.desc()).all()
    return {"sessions": sessions}

@router.post("/sessions/{session_id}/notes")
def add_session_note(
    session_id: int,
    note_data: dict,
    current_user = Depends(get_current_tutor),
    db: Session = Depends(get_db)
):
    """세션 노트 추가"""
    note = TutorNote(
        tutor_session_id=session_id,
        author_id=current_user.id,
        note_type=note_data["note_type"],
        title=note_data.get("title"),
        content=note_data["content"],
        is_visible_to_student=note_data.get("is_visible_to_student", True),
        is_visible_to_parent=note_data.get("is_visible_to_parent", True)
    )
    db.add(note)
    db.commit()
    return {"note_id": note.id}
```

## Policy/Approval 연동

### 1. 튜터 매칭 승인

```python
from app.models import Approval, AuditLog

# 학부모가 튜터 매칭 요청
approval = Approval(
    request_type="tutor_match",
    requester_id=parent_user_id,
    approver_role="admin",
    resource_type="tutor",
    resource_id=tutor_id,
    request_data={
        "student_id": student_id,
        "subjects": ["math"],
        "weekly_hours": 3,
        "rate_per_hour": 50000
    }
)
db.add(approval)
db.commit()

# 관리자 승인
approval.status = "approved"
approval.approved_by = admin_user_id
approval.approved_at = datetime.utcnow()
db.commit()

# TutorStudentRelation 자동 생성
if approval.status == "approved":
    relation = TutorStudentRelation(
        tutor_id=tutor_id,
        student_id=student_id,
        status="active",
        **approval.request_data
    )
    db.add(relation)
    db.commit()

# 감사 로그
audit = AuditLog(
    user_id=admin_user_id,
    event_type="tutor_match_approved",
    resource_type="tutor_student_relation",
    resource_id=relation.id,
    action="approve",
    description=f"Tutor {tutor_id} matched with student {student_id}"
)
db.add(audit)
db.commit()
```

### 2. 세션 생성/수정 감사

```python
# 세션 생성 시 자동 로깅
def create_tutor_session(session_data, current_user, db):
    session = TutorSession(**session_data)
    db.add(session)
    db.commit()
    
    # 감사 로그
    audit = AuditLog(
        user_id=current_user.id,
        event_type="tutor_session_created",
        resource_type="tutor_session",
        resource_id=session.id,
        action="create",
        details_json={
            "tutor_id": session.tutor_id,
            "student_id": session.student_id,
            "date": str(session.date),
            "subject": session.subject
        }
    )
    db.add(audit)
    db.commit()
    
    return session
```

## 대시보드 연동

### 튜터 대시보드 API

```python
@router.get("/dashboard/tutor/students")
def get_tutor_students(
    current_user = Depends(get_current_tutor),
    db: Session = Depends(get_db)
):
    """튜터가 담당하는 학생 목록"""
    tutor = db.query(Tutor).filter_by(user_id=current_user.id).first()
    
    relations = db.query(TutorStudentRelation).filter(
        TutorStudentRelation.tutor_id == tutor.id,
        TutorStudentRelation.status == 'active'
    ).all()
    
    students = []
    for rel in relations:
        # 최근 세션 정보
        last_session = db.query(TutorSession).filter(
            TutorSession.tutor_id == current_user.id,
            TutorSession.student_id == rel.student_id
        ).order_by(TutorSession.date.desc()).first()
        
        # CAT 시험 최근 점수 (기존 dashboard API 재사용)
        exam_summary = db.query(ExamSession).filter(
            ExamSession.student_id == rel.student_id,
            ExamSession.status == 'completed'
        ).order_by(ExamSession.ended_at.desc()).first()
        
        students.append({
            "student_id": rel.student_id,
            "student_name": rel.student.user.full_name,
            "subjects": rel.subjects,
            "weekly_hours": rel.weekly_hours,
            "last_session": {
                "date": last_session.date if last_session else None,
                "topic": last_session.topic if last_session else None
            },
            "recent_exam": {
                "score": exam_summary.score if exam_summary else None,
                "grade": exam_summary.meta.get('grade_letter') if exam_summary else None
            }
        })
    
    return {"students": students}
```

## 프론트엔드 컴포넌트

### TutorDashboard.tsx (이미 생성됨)

기존 `/frontend/components/dashboard/TutorDashboard.tsx`는 CAT 시험 결과를 보여줍니다.

튜터 세션 기능을 추가하려면:

```typescript
// TutorSessionList.tsx
import React from 'react';
import axios from 'axios';

export const TutorSessionList: React.FC = () => {
  const [sessions, setSessions] = useState([]);
  
  useEffect(() => {
    const fetchSessions = async () => {
      const res = await axios.get('/api/tutors/sessions', {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSessions(res.data.sessions);
    };
    fetchSessions();
  }, []);
  
  return (
    <div className="space-y-4">
      {sessions.map(session => (
        <div key={session.id} className="border rounded p-4">
          <div className="flex justify-between">
            <div>
              <h3 className="font-semibold">{session.subject}</h3>
              <p className="text-sm text-gray-600">{session.topic}</p>
            </div>
            <div className="text-right">
              <p className="text-sm">{session.date}</p>
              <span className={`badge ${session.status}`}>
                {session.status}
              </span>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};
```

## 데이터베이스 뷰 활용

```sql
-- 활성 튜터 목록
SELECT * FROM v_active_tutors
WHERE rating_avg >= 4.0
ORDER BY rating_count DESC;

-- 다가오는 세션
SELECT * FROM v_upcoming_tutor_sessions
WHERE date >= CURRENT_DATE
LIMIT 10;

-- 튜터 세션 요약
SELECT * FROM v_tutor_session_summary
WHERE tutor_id = 123
ORDER BY date DESC;
```

## 마이그레이션

```bash
# SQL 직접 실행
psql -U postgres -d dreamseed_dev < ops/sql/tutor_schema.sql

# 또는 Alembic
cd backend
alembic revision --autogenerate -m "Add tutor domain"
alembic upgrade head
```

## 테스트

```python
# backend/tests/test_tutors.py
def test_create_tutor(db_session):
    tutor = Tutor(
        user_id=1,
        subjects=['math'],
        hourly_rate=50000,
        is_active=True
    )
    db_session.add(tutor)
    db_session.commit()
    
    assert tutor.id is not None
    assert tutor.rating_avg == 0.0

def test_tutor_session_workflow(db_session):
    session = TutorSession(
        tutor_id=1,
        student_id=2,
        date=date.today(),
        status="upcoming"
    )
    db_session.add(session)
    db_session.commit()
    
    # 세션 시작
    session.status = "in_progress"
    session.started_at = datetime.utcnow()
    
    # 세션 완료
    session.status = "completed"
    session.ended_at = datetime.utcnow()
    
    db_session.commit()
    assert session.status == "completed"
```

## 다음 단계

1. **API 라우터 구현** (`backend/app/api/routers/tutors.py`)
2. **서비스 레이어** (`backend/app/services/tutor_service.py`)
3. **승인 워크플로우** 연동
4. **프론트엔드** 세션 관리 UI
5. **알림 시스템** (세션 알림, 과제 알림)
6. **결제 연동** (시간당 수업료 정산)

## 참고

- Teacher vs Tutor 구분을 명확히 유지
- Approval 시스템으로 매칭 승인 관리
- AuditLog로 모든 세션 활동 추적
- TutorLog (AI 튜터)와 TutorSession (사람 튜터) 분리
