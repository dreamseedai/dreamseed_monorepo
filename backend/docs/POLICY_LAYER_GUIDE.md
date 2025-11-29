# Policy, Approval & Audit Layer Implementation Guide

## 개요

정책/승인/감사 레이어는 DreamSeed CAT 시스템에 엔터프라이즈급 거버넌스 기능을 제공합니다:

- **AuditLog**: 모든 중요 이벤트 추적
- **Approval**: 재시험, 특별 접근 등 승인 워크플로우
- **ParentApproval**: 학부모-자녀 계정 연결 승인
- **StudentPolicy**: AI 튜터 사용 정책 제어
- **TutorLog**: AI 대화 품질 모니터링
- **StudentConsent**: GDPR/COPPA 동의 관리
- **DeletionRequest**: "잊힐 권리" 데이터 삭제

## 파일 구조

```
dreamseed_monorepo/
├── ops/sql/
│   └── policy_schema.sql          # PostgreSQL DDL 스키마
└── backend/app/
    └── models/
        └── policy.py               # SQLAlchemy ORM 모델
```

## 설치 및 마이그레이션

### 1. 직접 SQL 실행 (개발/테스트)

```bash
# PostgreSQL에 직접 적용
psql -U postgres -d dreamseed_dev < ops/sql/policy_schema.sql
```

### 2. Alembic Migration 생성 (프로덕션)

```bash
cd backend

# 새 마이그레이션 생성
alembic revision --autogenerate -m "Add policy approval audit layer"

# 마이그레이션 적용
alembic upgrade head
```

### 3. 모델 Import

```python
# backend/app/models/__init__.py
from app.models.policy import (
    AuditLog,
    Approval,
    ParentApproval,
    StudentPolicy,
    TutorLog,
    StudentConsent,
    DeletionRequest,
)
```

## 사용 예시

### 1. AuditLog - 감사 추적

```python
from app.models.policy import AuditLog
from app.core.database import get_db

# 데이터 접근 기록
audit = AuditLog(
    user_id=current_user.id,
    org_id=current_user.org_id,
    event_type="data_access",
    resource_type="exam_session",
    resource_id=exam_session_id,
    action="read",
    description="Teacher viewed student exam results",
    details_json={
        "student_id": student_id,
        "score": 85.5,
        "grade": "A"
    },
    ip_address=request.client.host,
    user_agent=request.headers.get("user-agent")
)
db.add(audit)
db.commit()

# 정책 위반 기록
audit = AuditLog(
    student_id=student_id,
    event_type="policy_violation",
    resource_type="ai_tutor",
    action="blocked",
    description="AI tutor access blocked during active exam",
    details_json={"exam_session_id": exam_session_id}
)
```

### 2. Approval - 재시험 승인

```python
from app.models.policy import Approval

# 학생이 재시험 요청
approval = Approval(
    request_type="retest",
    requester_id=student_user_id,
    approver_role="teacher",
    resource_type="exam",
    resource_id=exam_session_id,
    request_data={
        "reason": "기술적 문제로 인한 중단",
        "exam_name": "수학 중간고사",
        "original_score": 65.5
    },
    expires_at=datetime.utcnow() + timedelta(days=7)
)
db.add(approval)
db.commit()

# 교사가 승인 처리
approval = db.query(Approval).get(approval_id)
approval.status = "approved"
approval.approved_by = teacher_user_id
approval.approved_at = datetime.utcnow()
db.commit()

# 감사 로그 자동 생성
audit = AuditLog(
    user_id=teacher_user_id,
    event_type="approval_processed",
    resource_type="approval",
    resource_id=approval.id,
    action="approve",
    description=f"Retest request approved for exam #{exam_session_id}"
)
```

### 3. ParentApproval - 학부모 연결

```python
from app.models.policy import ParentApproval

# 학부모가 자녀 연결 요청
parent_approval = ParentApproval(
    parent_user_id=parent_user_id,
    student_id=student_id,
    status="pending"
)
db.add(parent_approval)
db.commit()

# 관리자/교사가 승인
parent_approval.status = "approved"
parent_approval.approved_by = admin_user_id
parent_approval.approved_at = datetime.utcnow()
db.commit()
```

### 4. StudentPolicy - AI 사용 제어

```python
from app.models.policy import StudentPolicy

# 학생별 정책 생성
policy = StudentPolicy(
    student_id=student_id,
    ai_tutor_enabled=True,
    daily_question_limit=20,
    restricted_during_exam=True,
    updated_by=teacher_user_id,
    meta={
        "plan": "standard",
        "restrictions": ["no_essay_generation", "no_exam_answers"]
    }
)
db.add(policy)
db.commit()

# 정책 확인
def can_use_ai_tutor(student_id: int, db: Session) -> bool:
    policy = db.query(StudentPolicy).filter_by(student_id=student_id).first()
    if not policy or not policy.ai_tutor_enabled:
        return False
    
    # 시험 중인지 확인
    if policy.restricted_during_exam:
        active_exam = db.query(ExamSession).filter(
            ExamSession.student_id == student_id,
            ExamSession.status == "in_progress"
        ).first()
        if active_exam:
            return False
    
    # 일일 제한 확인
    if policy.daily_question_limit:
        today_count = db.query(TutorLog).filter(
            TutorLog.student_id == student_id,
            TutorLog.created_at >= datetime.utcnow().date()
        ).count()
        if today_count >= policy.daily_question_limit:
            return False
    
    return True
```

### 5. TutorLog - AI 대화 기록

```python
from app.models.policy import TutorLog

# AI 튜터 대화 기록
tutor_log = TutorLog(
    student_id=student_id,
    session_id=tutor_session_id,
    question="이차방정식을 어떻게 풀어요?",
    answer="이차방정식 ax²+bx+c=0을 푸는 방법은...",
    model_used="gpt-4",
    context_json={
        "topic": "algebra",
        "difficulty": "intermediate",
        "related_items": [101, 102, 103]
    }
)
db.add(tutor_log)
db.commit()

# 품질 모니터링 쿼리
def get_tutor_quality_metrics(db: Session, date_from: datetime):
    """AI 튜터 품질 메트릭"""
    logs = db.query(TutorLog).filter(
        TutorLog.created_at >= date_from
    ).all()
    
    return {
        "total_questions": len(logs),
        "students_served": len(set(log.student_id for log in logs)),
        "avg_response_length": sum(len(log.answer or "") for log in logs) / len(logs),
        "models_used": dict(Counter(log.model_used for log in logs))
    }
```

### 6. StudentConsent - 동의 관리

```python
from app.models.policy import StudentConsent

# 동의 부여
consent = StudentConsent(
    student_id=student_id,
    parent_user_id=parent_user_id,
    consent_type="ai_usage",
    status="granted",
    granted_at=datetime.utcnow(),
    meta={
        "ip_address": request.client.host,
        "consent_text": "AI 튜터 사용에 동의합니다."
    }
)
db.add(consent)
db.commit()

# 동의 철회
consent.status = "revoked"
consent.revoked_at = datetime.utcnow()
db.commit()

# 동의 확인
def has_consent(student_id: int, consent_type: str, db: Session) -> bool:
    consent = db.query(StudentConsent).filter(
        StudentConsent.student_id == student_id,
        StudentConsent.consent_type == consent_type,
        StudentConsent.status == "granted"
    ).first()
    return consent is not None
```

### 7. DeletionRequest - 데이터 삭제

```python
from app.models.policy import DeletionRequest

# 삭제 요청 생성
deletion = DeletionRequest(
    student_id=student_id,
    requested_by=parent_user_id,
    reason="GDPR Right to be Forgotten",
    status="pending",
    meta={
        "data_types": ["exam_sessions", "tutor_logs", "personal_info"],
        "retention_period_expired": True
    }
)
db.add(deletion)
db.commit()

# 관리자 승인
deletion.status = "approved"
deletion.approved_by = admin_user_id
deletion.approved_at = datetime.utcnow()
db.commit()

# 데이터 삭제 처리
def process_deletion(deletion_id: int, db: Session):
    deletion = db.query(DeletionRequest).get(deletion_id)
    if deletion.status != "approved":
        raise ValueError("Deletion not approved")
    
    student_id = deletion.student_id
    
    # 데이터 삭제 (CASCADE로 자동 삭제되는 것도 많음)
    db.query(ExamSession).filter_by(student_id=student_id).delete()
    db.query(TutorLog).filter_by(student_id=student_id).delete()
    db.query(StudentConsent).filter_by(student_id=student_id).delete()
    # ... 기타 데이터
    
    # 완료 표시
    deletion.status = "done"
    deletion.processed_at = datetime.utcnow()
    db.commit()
    
    # 감사 로그
    audit = AuditLog(
        user_id=deletion.requested_by,
        event_type="data_deletion",
        resource_type="student",
        resource_id=student_id,
        action="delete",
        description="Student data deleted per GDPR request"
    )
    db.add(audit)
    db.commit()
```

## API 엔드포인트 예시

### 승인 관리 API

```python
# backend/app/api/routers/approvals.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.models.policy import Approval
from app.core.database import get_db

router = APIRouter(prefix="/api/approvals", tags=["approvals"])

@router.post("/request")
def request_approval(
    request_type: str,
    resource_type: str,
    resource_id: int,
    reason: str,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """승인 요청 생성"""
    approval = Approval(
        request_type=request_type,
        requester_id=current_user.id,
        approver_role="teacher",
        resource_type=resource_type,
        resource_id=resource_id,
        request_data={"reason": reason}
    )
    db.add(approval)
    db.commit()
    return {"approval_id": approval.id, "status": "pending"}

@router.get("/pending")
def get_pending_approvals(
    current_user = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """대기 중인 승인 목록"""
    approvals = db.query(Approval).filter(
        Approval.status == "pending",
        Approval.approver_role == current_user.role
    ).all()
    return {"approvals": approvals}

@router.post("/{approval_id}/approve")
def approve_request(
    approval_id: int,
    current_user = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    """승인 처리"""
    approval = db.query(Approval).get(approval_id)
    approval.status = "approved"
    approval.approved_by = current_user.id
    approval.approved_at = datetime.utcnow()
    db.commit()
    
    # 감사 로그
    audit = AuditLog(
        user_id=current_user.id,
        event_type="approval_processed",
        resource_id=approval_id,
        action="approve"
    )
    db.add(audit)
    db.commit()
    
    return {"status": "approved"}
```

## 데이터베이스 뷰 활용

```python
# 대기 중인 승인 조회
pending = db.execute("SELECT * FROM v_pending_approvals").fetchall()

# 최근 감사 이벤트
recent_audits = db.execute("SELECT * FROM v_recent_audit_events").fetchall()

# 학생 정책 요약
policies = db.execute("SELECT * FROM v_student_policy_summary").fetchall()
```

## 보안 고려사항

1. **감사 로그 보호**
   - AuditLog는 수정/삭제 불가 (append-only)
   - 별도 읽기 전용 replica 고려
   - 정기적 아카이브 및 백업

2. **승인 만료**
   - `expires_at` 자동 정리 cron job
   - 만료된 승인은 자동으로 `expired` 상태로 변경

3. **동의 철회 즉시 반영**
   - StudentConsent 변경 시 즉시 캐시 무효화
   - AI 튜터 접근 전 매번 동의 확인

4. **삭제 요청 2단계 승인**
   - 학부모 요청 → 관리자 승인 → 실제 삭제
   - 삭제 전 최종 확인 이메일 발송

## 모니터링 쿼리

```sql
-- 일일 감사 이벤트 통계
SELECT event_type, COUNT(*) as count
FROM audit_logs
WHERE timestamp >= NOW() - INTERVAL '1 day'
GROUP BY event_type
ORDER BY count DESC;

-- 대기 중인 승인 (긴급)
SELECT * FROM v_pending_approvals
WHERE hours_pending > 24
ORDER BY created_at ASC;

-- AI 튜터 사용률
SELECT COUNT(DISTINCT student_id) as active_students,
       COUNT(*) as total_questions
FROM tutor_logs
WHERE created_at >= NOW() - INTERVAL '1 day';

-- 정책 위반 발생률
SELECT COUNT(*) as violations
FROM audit_logs
WHERE event_type = 'policy_violation'
  AND timestamp >= NOW() - INTERVAL '1 day';
```

## 다음 단계

1. **API 라우터 구현**
   - `backend/app/api/routers/approvals.py`
   - `backend/app/api/routers/policies.py`
   - `backend/app/api/routers/audit.py`

2. **서비스 레이어**
   - `backend/app/services/approval_service.py`
   - `backend/app/services/policy_service.py`
   - `backend/app/services/audit_service.py`

3. **테스트**
   - `backend/tests/test_approvals.py`
   - `backend/tests/test_policies.py`
   - `backend/tests/test_audit.py`

4. **프론트엔드**
   - 승인 관리 대시보드
   - 정책 설정 UI
   - 감사 로그 뷰어

## 참고 문서

- [GDPR Compliance](https://gdpr.eu/)
- [COPPA Guidelines](https://www.ftc.gov/business-guidance/resources/childrens-online-privacy-protection-rule-not-just-kids-sites)
- [SQLAlchemy ORM](https://docs.sqlalchemy.org/en/20/orm/)
- [PostgreSQL JSONB](https://www.postgresql.org/docs/current/datatype-json.html)
