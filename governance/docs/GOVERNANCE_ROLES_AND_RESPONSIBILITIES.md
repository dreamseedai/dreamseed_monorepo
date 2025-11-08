# DreamSeedAI: 거버넌스 계층 - 역할과 책임 구조 상세

**작성일**: 2025-11-07  
**버전**: 1.0.0  
**관련 문서**: [거버넌스 계층 운영](./GOVERNANCE_LAYER_OPERATIONS.md), [거버넌스 계층 상세 설계](./GOVERNANCE_LAYER_DETAILED.md)

---

## 개요

DreamSeedAI의 거버넌스 계층은 **플랫폼 내 각 이해관계자(교사, 학부모, 관리자, 학생)의 역할과 책임 구조를 명확히 정의**합니다. 

이러한 정의는 각 사용자가 시스템을 **안전하고 효과적으로 사용**할 수 있도록 보장하며, **책임 소재를 명확히** 합니다.

---

## 1. 주요 역할

### 1.1 관리자 (Administrator)

#### 플랫폼 관리자 (Platform Administrator)

**책임**:
- 플랫폼 전체 운영 및 관리
- 전체 사용자 계정 관리
- 시스템 설정 변경 및 정책 적용
- 데이터 보안 및 개인정보 보호 유지
- 시스템 성능 모니터링 및 최적화
- 거버넌스 정책 준수 감독

**권한**:
- 시스템의 모든 기능에 접근 가능
- 글로벌 설정 변경 권한
- 모든 사용자 계정 관리 권한
- 시스템 로그 및 감사 로그 조회 권한
- 정책 설정 변경 권한
- **단, 개인정보(PII)는 긴급 상황 시 거버넌스 위원회 승인 필요**

**주요 활동**:
```yaml
platform_admin_activities:
  daily:
    - "시스템 상태 모니터링"
    - "보안 알림 확인 및 대응"
    - "긴급 이슈 처리"
    
  weekly:
    - "사용자 계정 검토 및 정리"
    - "시스템 성능 분석"
    - "정책 위반 사례 검토"
    
  monthly:
    - "보안 감사 실시"
    - "백업 및 복구 테스트"
    - "정책 준수 보고서 작성"
    
  quarterly:
    - "시스템 업그레이드 계획"
    - "거버넌스 위원회 보고"
```

#### 학교 관리자 (School Administrator)

**책임**:
- 소속 학교 내 플랫폼 운영
- 학교 교사 및 학생 계정 관리
- 학교별 정책 설정
- 학교 데이터 관리

**권한**:
- 소속 학교 데이터 접근
- 학교 교사 계정 생성 및 관리
- 학급 편성 관리
- 학교별 콘텐츠 설정
- **타 학교 데이터 접근 불가**

**접근 제한**:
```python
# 학교 관리자 권한 제한 (Row-Level Security)
@app.get("/api/schools/{school_id}/students")
async def get_school_students(
    school_id: str,
    admin: User = Depends(get_current_user)
):
    # 본인 학교만 접근 가능
    if admin.role != "school_admin" or admin.school_id != school_id:
        raise HTTPException(403, "권한 없음")
    
    students = db.query(Student).filter(
        Student.school_id == school_id
    ).all()
    
    return students
```

---

### 1.2 교사 (Teacher)

**책임**:
- 담당 학급 학생들의 학습 지도 및 평가
- **AI 추천 콘텐츠 검토 및 승인** (Human-in-the-Loop)
- 학생 데이터 분석 및 맞춤 학습 계획 수립
- 학생들의 질문에 답변하고 학습 어려움 지원
- AI 시스템의 오작동 또는 오류 발견 시 보고
- 학부모와의 소통 및 학습 현황 공유

**권한**:
- 담당 학급 학생들의 학습 데이터 접근 가능
- AI 추천 콘텐츠 검토, 승인, 거부, 수정 권한
- 과제 및 평가 생성 권한
- 학생 성적 입력 및 수정 권한
- 학생 관찰 기록 작성 권한
- **타 학급 데이터 접근 불가**

**주요 활동**:
```yaml
teacher_activities:
  daily:
    - "AI 추천 콘텐츠 검토 및 승인"
    - "학생 질문 답변"
    - "학습 진행 상황 모니터링"
    
  weekly:
    - "학급 전체 학습 분석"
    - "맞춤 과제 생성"
    - "학부모 소통"
    
  monthly:
    - "학생별 성취도 평가"
    - "학습 계획 수정"
    - "학급 보고서 작성"
```

**AI 콘텐츠 승인 워크플로우**:
```python
# 교사의 AI 콘텐츠 승인 권한
@app.post("/api/approvals/{approval_id}/approve")
async def approve_ai_content(
    approval_id: str,
    teacher: User = Depends(get_current_user),
    comment: str = None
):
    # 교사만 승인 가능
    if teacher.role != "teacher":
        raise HTTPException(403, "교사만 승인 가능")
    
    approval = db.query(ApprovalRequest).get(approval_id)
    
    # 담당 학급 학생만 승인 가능
    student = db.query(Student).get(approval.student_id)
    if student.teacher_id != teacher.id:
        raise HTTPException(403, "담당 학생이 아닙니다")
    
    # 승인 처리
    approval.status = "approved"
    approval.approved_by = teacher.id
    approval.approved_at = datetime.utcnow()
    approval.teacher_comment = comment
    
    db.session.commit()
    
    # 감사 로그
    audit_logger.log_approval(
        approval_type="ai_content",
        approver_id=teacher.id,
        request_id=approval_id,
        decision="approved",
        comment=comment
    )
    
    return {"status": "approved"}
```

---

### 1.3 학부모 (Parent)

**책임**:
- 자녀의 학습 진행 상황 확인
- 개인정보 제공 동의 관리
- 자녀의 학습 환경 지원
- 부적절한 콘텐츠 발견 시 신고

**권한**:
- **자녀의 학습 데이터 접근 가능**
  - 학습 진행 상황
  - 평가 결과
  - AI 튜터와의 대화 기록 (동의한 경우)
- **데이터 수집 및 사용 동의 관리**
  - 동의 항목별 선택 가능
  - 언제든지 동의 철회 가능
- **데이터 관리 권한**
  - 수집된 데이터 삭제 요청
  - 잘못된 정보 수정 요청
  - 데이터 이동(portability) 요청
- **타 자녀 데이터 접근 불가**

**주요 권리** (GDPR, COPPA, FERPA 기반):
```yaml
parent_rights:
  right_to_access:
    description: "자녀 데이터 열람 권한"
    scope:
      - "학습 기록"
      - "평가 결과"
      - "AI 상호작용 기록"
      - "정서 로그 (동의한 경우)"
    
  right_to_rectification:
    description: "부정확한 정보 수정 요청 권한"
    process: "요청 후 7일 이내 처리"
    
  right_to_erasure:
    description: "데이터 삭제 요청 권한 (잊힐 권리)"
    process: "요청 후 30일 이내 완전 삭제"
    exceptions:
      - "법적 의무 보관 기간"
      - "학교 기록 보존 정책"
      
  right_to_data_portability:
    description: "데이터 이동 권한"
    format: "JSON, CSV"
    delivery: "이메일 또는 다운로드"
    
  right_to_object:
    description: "데이터 처리 반대 권한"
    scope:
      - "AI 분석 거부"
      - "마케팅 활용 거부"
      
  right_to_withdraw_consent:
    description: "동의 철회 권한"
    effect: "즉시 데이터 수집 중단 및 삭제"
```

**동의 관리 인터페이스**:
```typescript
// 학부모 동의 관리 UI
interface ParentConsentManager {
    // 동의 항목
    consents: {
        essential: {
            data_collection: boolean;  // 필수 (서비스 제공)
            educational_use: boolean;  // 필수
        };
        optional: {
            ai_tutoring: boolean;      // 선택
            mood_tracking: boolean;    // 선택
            analytics: boolean;        // 선택
            research: boolean;         // 선택
        };
    };
    
    // 동의 이력
    history: ConsentHistory[];
    
    // 동의 변경
    updateConsent(type: string, value: boolean): Promise<void>;
    
    // 자녀 데이터 조회
    viewChildData(childId: string): Promise<StudentData>;
    
    // 데이터 삭제 요청
    requestDataDeletion(childId: string, reason: string): Promise<DeletionRequest>;
    
    // 데이터 다운로드
    downloadChildData(childId: string, format: 'json' | 'csv'): Promise<File>;
}
```

---

### 1.4 학생 (Student)

**책임**:
- 학습 활동 참여
- AI 튜터 적극 활용
- 피드백 제공 (콘텐츠 평가, 만족도 등)
- 부적절한 콘텐츠 신고

**권한**:
- **자신의 학습 데이터 접근 가능**
  - 학습 진행 상황 조회
  - 평가 결과 확인
  - AI 튜터 대화 기록 조회
- **개인정보 수정 요청 권한**
- **AI 추천 거부 권한**
- **학습 목표 설정 권한**
- **타 학생 데이터 접근 불가**

**학생 권리** (아동 보호 원칙):
```yaml
student_rights:
  right_to_privacy:
    description: "개인정보 보호 권리"
    protections:
      - "개인정보 최소 수집"
      - "데이터 암호화"
      - "접근 제어"
      
  right_to_safety:
    description: "안전한 학습 환경 권리"
    protections:
      - "유해 콘텐츠 완전 차단"
      - "괴롭힘 방지"
      - "정서적 안정 모니터링"
      
  right_to_explanation:
    description: "AI 결정 설명 받을 권리"
    implementation:
      - "모든 AI 추천에 이유 설명"
      - "쉬운 언어로 제공"
      
  right_to_opt_out:
    description: "AI 기능 거부 권리"
    scope:
      - "AI 튜터 사용 거부 가능"
      - "AI 추천 거부 가능"
      - "전통적 학습 방식 선택 가능"
      
  right_to_access:
    description: "자기 데이터 열람 권리"
    scope: "자신의 모든 학습 기록"
```

---

## 2. 역할 기반 접근 제어 (RBAC) 정책

거버넌스 계층에서 정의된 역할과 책임은 **시스템 계층에서 역할 기반 접근 제어 (RBAC) 정책으로 구현**됩니다.

### 2.1 API 엔드포인트 접근 제한

각 API 엔드포인트는 **특정 역할에 대해서만 접근을 허용**하도록 설정됩니다.

**엔드포인트별 접근 권한 매핑**:
```yaml
# governance/policies/api_access_policy.yaml

api_endpoints:
  # 관리자 전용
  admin_only:
    - "/api/admin/users"
    - "/api/admin/system-settings"
    - "/api/admin/policies"
    - "/api/admin/audit-logs"
    allowed_roles: ["platform_admin"]
    
  # 학교 관리자
  school_admin:
    - "/api/schools/{school_id}/teachers"
    - "/api/schools/{school_id}/students"
    - "/api/schools/{school_id}/classes"
    allowed_roles: ["platform_admin", "school_admin"]
    constraints:
      - "school_id must match user.school_id"
      
  # 교사
  teacher:
    - "/api/classes/{class_id}/students"
    - "/api/approvals/{approval_id}/approve"
    - "/api/assignments"
    allowed_roles: ["platform_admin", "school_admin", "teacher"]
    constraints:
      - "class_id must be in teacher.class_ids"
      
  # 학부모
  parent:
    - "/api/students/{student_id}/data"
    - "/api/students/{student_id}/consents"
    - "/api/students/{student_id}/delete-request"
    allowed_roles: ["platform_admin", "parent"]
    constraints:
      - "student_id must be in parent.children_ids"
      
  # 학생
  student:
    - "/api/students/{student_id}/learning-data"
    - "/api/students/{student_id}/ai-tutor"
    - "/api/students/{student_id}/feedback"
    allowed_roles: ["platform_admin", "teacher", "parent", "student"]
    constraints:
      - "student_id must match user.id or user.children_ids"
      
  # 공개 (인증 필요)
  authenticated:
    - "/api/content/public"
    - "/api/profile"
    allowed_roles: ["all"]
```

**구현 예시**:
```python
# system/backend/middleware/rbac_middleware.py

from functools import wraps
from fastapi import HTTPException

def require_role(*allowed_roles):
    """역할 기반 접근 제어 데코레이터"""
    
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 현재 사용자 확인
            user = kwargs.get('user') or kwargs.get('current_user')
            
            if not user:
                raise HTTPException(401, "인증 필요")
            
            # 역할 확인
            if user.role not in allowed_roles:
                audit_logger.log_access_denied(
                    user_id=user.id,
                    endpoint=request.url.path,
                    required_roles=allowed_roles,
                    user_role=user.role
                )
                raise HTTPException(403, f"권한 없음. 필요 역할: {allowed_roles}")
            
            return await func(*args, **kwargs)
        
        return wrapper
    
    return decorator


# 사용 예시
@app.get("/api/admin/users")
@require_role("platform_admin")
async def get_all_users(user: User = Depends(get_current_user)):
    """관리자만 접근 가능"""
    return db.query(User).all()


@app.post("/api/approvals/{approval_id}/approve")
@require_role("teacher")
async def approve_content(
    approval_id: str,
    user: User = Depends(get_current_user)
):
    """교사만 승인 가능"""
    # ... 승인 로직
```

---

### 2.2 데이터 접근 범위 제한

사용자는 자신의 역할에 따라 **접근 가능한 데이터 범위가 제한**됩니다.

**데이터베이스 Row-Level Security (RLS)**:
```sql
-- PostgreSQL Row-Level Security 정책

-- 학생 데이터 접근 정책
CREATE POLICY student_data_access ON students
    FOR SELECT
    USING (
        -- 본인
        id = current_setting('app.current_user_id')::TEXT
        OR
        -- 담당 교사
        teacher_id = current_setting('app.current_user_id')::TEXT
        OR
        -- 학부모
        EXISTS (
            SELECT 1 FROM parent_children
            WHERE parent_id = current_setting('app.current_user_id')::TEXT
            AND child_id = students.id
        )
        OR
        -- 학교 관리자 (동일 학교)
        (
            current_setting('app.current_user_role') = 'school_admin'
            AND school_id = current_setting('app.current_user_school_id')::TEXT
        )
        OR
        -- 플랫폼 관리자
        current_setting('app.current_user_role') = 'platform_admin'
    );

-- 학습 기록 접근 정책
CREATE POLICY learning_records_access ON learning_records
    FOR SELECT
    USING (
        -- 학생 본인
        student_id = current_setting('app.current_user_id')::TEXT
        OR
        -- 담당 교사
        EXISTS (
            SELECT 1 FROM students
            WHERE students.id = learning_records.student_id
            AND students.teacher_id = current_setting('app.current_user_id')::TEXT
        )
        OR
        -- 학부모
        EXISTS (
            SELECT 1 FROM parent_children
            WHERE parent_id = current_setting('app.current_user_id')::TEXT
            AND child_id = learning_records.student_id
        )
    );

-- 교사 노트 접근 정책 (교사만)
CREATE POLICY teacher_notes_access ON teacher_notes
    FOR ALL
    USING (
        -- 작성한 교사 본인만
        teacher_id = current_setting('app.current_user_id')::TEXT
        OR
        -- 플랫폼 관리자
        current_setting('app.current_user_role') = 'platform_admin'
    );
```

**애플리케이션 레벨 데이터 필터링**:
```python
# system/backend/services/data_access_service.py

class DataAccessService:
    """역할 기반 데이터 접근 제어"""
    
    def get_accessible_students(self, user: User) -> list[Student]:
        """사용자가 접근 가능한 학생 목록"""
        
        if user.role == "platform_admin":
            # 플랫폼 관리자: 모든 학생
            return db.query(Student).all()
        
        elif user.role == "school_admin":
            # 학교 관리자: 소속 학교 학생만
            return db.query(Student).filter(
                Student.school_id == user.school_id
            ).all()
        
        elif user.role == "teacher":
            # 교사: 담당 학급 학생만
            return db.query(Student).filter(
                Student.teacher_id == user.id
            ).all()
        
        elif user.role == "parent":
            # 학부모: 자녀만
            return db.query(Student).join(ParentChild).filter(
                ParentChild.parent_id == user.id
            ).all()
        
        elif user.role == "student":
            # 학생: 본인만
            return [db.query(Student).get(user.id)]
        
        else:
            return []
    
    def filter_student_data(self, student_data: dict, user: User) -> dict:
        """역할에 따라 민감 데이터 필터링"""
        
        filtered_data = student_data.copy()
        
        if user.role == "parent":
            # 학부모는 교사 노트 볼 수 없음
            filtered_data.pop('teacher_notes', None)
            
            # 동의하지 않은 정서 로그 제외
            if not self._has_consent(student_data['id'], user.id, 'mood_logs'):
                filtered_data.pop('mood_logs', None)
        
        elif user.role == "student":
            # 학생은 자신의 IRT 능력 추정치 원시값 볼 수 없음
            # (해석된 결과만 표시)
            if 'theta' in filtered_data:
                filtered_data['ability_level'] = self._interpret_theta(filtered_data['theta'])
                filtered_data.pop('theta', None)
        
        return filtered_data
```

---

### 2.3 기능 사용 제한

특정 기능은 **특정 역할의 사용자만 사용**할 수 있도록 제한됩니다.

**기능별 역할 매핑**:
```yaml
# governance/policies/feature_access_policy.yaml

features:
  ai_content_approval:
    name: "AI 콘텐츠 승인"
    allowed_roles: ["teacher"]
    description: "교사만 AI 추천 콘텐츠를 승인/거부할 수 있음"
    
  student_account_creation:
    name: "학생 계정 생성"
    allowed_roles: ["platform_admin", "school_admin"]
    description: "관리자만 학생 계정을 생성할 수 있음"
    
  consent_management:
    name: "동의 관리"
    allowed_roles: ["parent"]
    description: "학부모만 자녀의 동의 설정을 변경할 수 있음"
    constraints:
      - "만 14세 미만 학생의 경우만"
      
  data_deletion_request:
    name: "데이터 삭제 요청"
    allowed_roles: ["parent", "student"]
    description: "학부모와 학생은 데이터 삭제를 요청할 수 있음"
    
  policy_configuration:
    name: "정책 설정"
    allowed_roles: ["platform_admin", "governance_board"]
    description: "플랫폼 관리자와 거버넌스 위원회만 정책을 설정할 수 있음"
    
  grade_input:
    name: "성적 입력"
    allowed_roles: ["teacher"]
    description: "교사만 학생 성적을 입력할 수 있음"
    
  ai_tutor_usage:
    name: "AI 튜터 사용"
    allowed_roles: ["student"]
    description: "학생만 AI 튜터를 사용할 수 있음"
    constraints:
      - "학부모 동의 필요 (만 14세 미만)"
```

---

## 3. 주요 권한 및 책임 상세

### 3.1 학부모 권한 및 책임

#### 접근 권한
```python
# 학부모가 접근 가능한 자녀 데이터
parent_accessible_data = {
    "basic_info": {
        "name": "홍길동",
        "grade": "중학교 2학년",
        "school": "서울중학교",
        "class": "2반"
    },
    
    "learning_progress": {
        "subjects": {
            "수학": {
                "completion_rate": 0.85,
                "average_score": 87,
                "recent_activities": [...]
            },
            # ...
        },
        "study_time_weekly": "평균 5시간 30분",
        "learning_streak": "연속 12일"
    },
    
    "assessment_results": {
        "recent_tests": [
            {
                "subject": "수학",
                "score": 90,
                "date": "2025-11-01",
                "feedback": "2차 방정식 문제 해결 능력 향상"
            },
            # ...
        ],
        "ability_estimate": "중상위권 (상위 30%)"
    },
    
    "ai_interactions": {
        "total_questions": 145,
        "ai_tutor_sessions": 23,
        "recent_conversations": [
            {
                "date": "2025-11-07",
                "topic": "이차함수 그래프",
                "duration": "15분",
                "summary": "y = ax² + bx + c 형태 그래프 그리기 학습"
            },
            # ...
        ]
    } if parent_has_consent("ai_tutoring") else None,
    
    "mood_logs": [
        {"date": "2025-11-07", "mood": 4, "comment": "오늘 수학 문제 잘 풀림!"},
        # ...
    ] if parent_has_consent("mood_tracking") else None
}
```

#### 동의 관리
```typescript
// 학부모 동의 관리 시스템
interface ParentConsentSystem {
    // 현재 동의 상태
    getCurrentConsents(childId: string): ConsentStatus;
    
    // 동의 변경
    updateConsent(childId: string, consentType: string, value: boolean): Promise<void>;
    
    // 동의 철회 (즉시 효력 발생)
    revokeConsent(childId: string, consentType: string): Promise<void>;
    
    // 동의 이력 조회
    getConsentHistory(childId: string): ConsentHistory[];
}

// 동의 철회 시 자동 처리
async function handleConsentRevocation(
    childId: string,
    consentType: string
) {
    // 1. 해당 데이터 수집 즉시 중단
    await stopDataCollection(childId, consentType);
    
    // 2. 기존 수집된 데이터 삭제 (30일 이내)
    await scheduleDataDeletion(childId, consentType, days: 30);
    
    // 3. 학부모에게 확인 이메일 발송
    await sendConsentRevocationConfirmation(childId, consentType);
    
    // 4. 감사 로그 기록
    auditLogger.log({
        action: "consent_revocation",
        child_id: childId,
        consent_type: consentType,
        timestamp: new Date()
    });
}
```

#### 데이터 삭제 요청
```python
# 학부모 데이터 삭제 요청 처리
@app.post("/api/students/{student_id}/delete-request")
async def request_data_deletion(
    student_id: str,
    parent: User = Depends(get_current_user),
    reason: str,
    delete_all: bool = True
):
    """학부모 데이터 삭제 요청"""
    
    # 1. 권한 확인 (본인 자녀만)
    if not is_parent_of(parent.id, student_id):
        raise HTTPException(403, "권한 없음")
    
    # 2. 삭제 요청 생성
    deletion_request = DataDeletionRequest(
        id=str(uuid.uuid4()),
        student_id=student_id,
        requester_id=parent.id,
        requester_type="parent",
        reason=reason,
        delete_all=delete_all,
        status="pending",
        created_at=datetime.utcnow(),
        scheduled_deletion_date=datetime.utcnow() + timedelta(days=30)
    )
    
    db.session.add(deletion_request)
    db.session.commit()
    
    # 3. 확인 이메일 발송
    await email_service.send(
        to=parent.email,
        subject="데이터 삭제 요청 접수",
        body=f"""
        자녀({student_id})의 데이터 삭제 요청이 접수되었습니다.
        
        - 삭제 예정일: {deletion_request.scheduled_deletion_date.strftime('%Y-%m-%d')}
        - 요청 사유: {reason}
        
        삭제 예정일 전까지 요청을 취소할 수 있습니다.
        """
    )
    
    # 4. 감사 로그
    audit_logger.log({
        "action": "data_deletion_request",
        "student_id": student_id,
        "requester_id": parent.id,
        "reason": reason
    })
    
    return {
        "status": "pending",
        "request_id": deletion_request.id,
        "scheduled_deletion_date": deletion_request.scheduled_deletion_date
    }
```

---

### 3.2 교사 권한 및 책임

#### AI 콘텐츠 승인 책임
```python
# 교사의 AI 콘텐츠 승인 프로세스
class TeacherApprovalWorkflow:
    """교사 승인 워크플로우"""
    
    async def review_ai_recommendation(
        self,
        teacher: User,
        approval_id: str
    ) -> dict:
        """AI 추천 검토"""
        
        approval = db.query(ApprovalRequest).get(approval_id)
        
        # 승인 대기 콘텐츠 정보
        recommendation = {
            "student": approval.student,
            "content_type": approval.recommendation['type'],
            "difficulty": approval.recommendation['difficulty'],
            "topic": approval.recommendation['topic'],
            "ai_explanation": approval.recommendation['explanation'],
            "safety_score": approval.recommendation['safety_score'],
            "estimated_time": approval.recommendation['estimated_time']
        }
        
        # 교사에게 검토 자료 제공
        return {
            "approval_id": approval_id,
            "recommendation": recommendation,
            "student_context": {
                "current_ability": approval.student.theta,
                "recent_performance": self._get_recent_performance(approval.student_id),
                "learning_style": approval.student.learning_style
            },
            "teacher_actions": {
                "approve": "콘텐츠 승인 (학생에게 즉시 제공)",
                "modify": "난이도 또는 수량 조정 후 승인",
                "reject": "다른 콘텐츠 추천 요청",
                "defer": "나중에 결정 (24시간 내)"
            }
        }
    
    async def approve_with_modification(
        self,
        teacher: User,
        approval_id: str,
        modifications: dict
    ):
        """수정 후 승인"""
        
        # 교사가 난이도 조정
        if 'difficulty_adjustment' in modifications:
            await ai_engine.adjust_difficulty(
                approval_id,
                adjustment=modifications['difficulty_adjustment']
            )
        
        # 교사가 수량 조정
        if 'quantity' in modifications:
            await ai_engine.adjust_quantity(
                approval_id,
                quantity=modifications['quantity']
            )
        
        # 승인 처리
        await self.approve(teacher, approval_id, modifications)
```

#### 학생 데이터 분석 책임
```python
# 교사의 학생 데이터 분석 도구
@app.get("/api/teachers/analytics/class/{class_id}")
async def get_class_analytics(
    class_id: str,
    teacher: User = Depends(get_current_user)
):
    """학급 전체 학습 분석"""
    
    # 권한 확인
    if not is_teacher_of_class(teacher.id, class_id):
        raise HTTPException(403, "담당 학급이 아닙니다")
    
    students = db.query(Student).filter(Student.class_id == class_id).all()
    
    analytics = {
        "class_overview": {
            "total_students": len(students),
            "average_ability": np.mean([s.theta for s in students]),
            "engagement_rate": calculate_engagement_rate(students),
            "completion_rate": calculate_completion_rate(students)
        },
        
        "performance_distribution": {
            "high_achievers": len([s for s in students if s.theta > 1.0]),
            "middle_performers": len([s for s in students if -0.5 <= s.theta <= 1.0]),
            "struggling_students": len([s for s in students if s.theta < -0.5])
        },
        
        "students_needing_attention": [
            {
                "student_id": s.id,
                "name": s.name,
                "reason": "학습 능력 하락 (최근 7일)",
                "theta_change": s.theta - s.theta_7days_ago,
                "recommended_action": "1:1 상담 및 맞춤 지도"
            }
            for s in students
            if (s.theta - s.theta_7days_ago) < -0.3
        ],
        
        "ai_recommendations": {
            "pending_approvals": db.query(ApprovalRequest).filter(
                ApprovalRequest.status == "pending",
                ApprovalRequest.teacher_id == teacher.id
            ).count(),
            
            "suggested_interventions": ai_engine.suggest_interventions(class_id)
        }
    }
    
    return analytics
```

#### AI 오작동 보고 책임
```python
# 교사의 AI 오작동 신고 시스템
@app.post("/api/teachers/report-ai-issue")
async def report_ai_issue(
    teacher: User = Depends(get_current_user),
    issue_type: str,
    student_id: str,
    description: str,
    severity: str
):
    """AI 시스템 오작동 보고"""
    
    issue_report = AIIssueReport(
        id=str(uuid.uuid4()),
        reporter_id=teacher.id,
        reporter_type="teacher",
        issue_type=issue_type,  # "incorrect_recommendation", "safety_violation", etc.
        student_id=student_id,
        description=description,
        severity=severity,  # "low", "medium", "high", "critical"
        status="open",
        created_at=datetime.utcnow()
    )
    
    db.session.add(issue_report)
    db.session.commit()
    
    # 심각도에 따라 즉시 알림
    if severity in ["high", "critical"]:
        await alert_ai_team(issue_report)
        
        # 해당 학생에 대한 AI 추천 일시 중단
        await suspend_ai_recommendations(student_id)
    
    return {
        "status": "reported",
        "issue_id": issue_report.id,
        "next_steps": "AI 팀이 24시간 내 검토 예정"
    }
```

---

### 3.3 관리자 권한 및 책임

#### 시스템 보안 유지 책임
```python
# 관리자 보안 모니터링 대시보드
@app.get("/api/admin/security/dashboard")
async def security_dashboard(
    admin: User = Depends(require_platform_admin)
):
    """보안 모니터링 대시보드"""
    
    now = datetime.utcnow()
    
    return {
        "security_events": {
            "last_24h": {
                "failed_login_attempts": get_failed_logins(hours=24),
                "unauthorized_access_attempts": get_access_denied(hours=24),
                "policy_violations": get_policy_violations(hours=24),
                "data_breach_attempts": get_breach_attempts(hours=24)
            },
            
            "active_threats": get_active_threats(),
            
            "vulnerability_scan": {
                "last_scan": get_last_vulnerability_scan(),
                "critical_vulnerabilities": 0,
                "high_vulnerabilities": 2,
                "status": "패치 진행 중"
            }
        },
        
        "data_protection": {
            "encryption_status": "active",
            "backup_status": get_backup_status(),
            "last_backup": get_last_backup_time(),
            "pii_access_logs": get_pii_access_count(hours=24)
        },
        
        "compliance_status": {
            "gdpr": "compliant",
            "coppa": "compliant",
            "ferpa": "compliant",
            "last_audit": "2025-10-15"
        }
    }
```

#### AI 공정성 검토 책임
```python
# 관리자 AI 공정성 검토
@app.get("/api/admin/ai/fairness-audit")
async def ai_fairness_audit(
    admin: User = Depends(require_platform_admin)
):
    """AI 공정성 감사"""
    
    # 그룹별 성과 분석
    fairness_metrics = {
        "demographic_parity": calculate_demographic_parity(),
        "equal_opportunity": calculate_equal_opportunity(),
        
        "performance_by_group": {
            "gender": {
                "male": {"avg_theta": 0.45, "recommendation_rate": 0.82},
                "female": {"avg_theta": 0.48, "recommendation_rate": 0.84}
            },
            "region": {
                "urban": {"avg_theta": 0.52, "recommendation_rate": 0.85},
                "rural": {"avg_theta": 0.41, "recommendation_rate": 0.79}
            }
        },
        
        "bias_indicators": {
            "gender_bias_score": 0.03,  # < 0.05 목표
            "regional_bias_score": 0.11,  # ⚠️ 임계값 초과
            "status": "조치 필요"
        },
        
        "recommended_actions": [
            {
                "issue": "지역별 추천 빈도 격차",
                "action": "농촌 지역 학생 대상 콘텐츠 추천 강화",
                "priority": "high"
            }
        ]
    }
    
    return fairness_metrics
```

---

## 4. 구현 메커니즘

### 4.1 API Gateway

**사용자 인증 및 권한 검사**를 수행하고, 요청을 적절한 서비스로 라우팅합니다.

```python
# infra/api_gateway/gateway.py

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import httpx

app = FastAPI()

class APIGateway:
    """API Gateway - 인증, 권한 검사, 라우팅"""
    
    def __init__(self):
        self.policy_engine = PolicyEngine()
        self.auth_service_url = "http://auth-service:8000"
        self.backend_service_url = "http://backend-service:8001"
    
    async def authenticate(self, request: Request) -> User:
        """OIDC 기반 사용자 인증"""
        
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            raise HTTPException(401, "인증 토큰 필요")
        
        # OIDC 토큰 검증
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.auth_service_url}/verify",
                headers={"Authorization": auth_header}
            )
        
        if response.status_code != 200:
            raise HTTPException(401, "유효하지 않은 토큰")
        
        user_data = response.json()
        return User(**user_data)
    
    async def authorize(self, user: User, request: Request) -> bool:
        """역할 기반 권한 검사"""
        
        # 정책 엔진을 통한 권한 확인
        return self.policy_engine.check_access_policy(
            user=user,
            resource=request.url.path,
            action=request.method
        )
    
    async def route_request(self, request: Request, user: User):
        """요청 라우팅"""
        
        # 백엔드 서비스로 전달
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method=request.method,
                url=f"{self.backend_service_url}{request.url.path}",
                headers={
                    "X-User-ID": user.id,
                    "X-User-Role": user.role,
                    "X-School-ID": user.school_id
                },
                content=await request.body()
            )
        
        return JSONResponse(
            content=response.json(),
            status_code=response.status_code
        )


@app.middleware("http")
async def gateway_middleware(request: Request, call_next):
    """게이트웨이 미들웨어"""
    
    gateway = APIGateway()
    
    # 1. 인증
    user = await gateway.authenticate(request)
    
    # 2. 권한 검사
    if not await gateway.authorize(user, request):
        return JSONResponse(
            {"error": "권한 없음"},
            status_code=403
        )
    
    # 3. 라우팅
    return await gateway.route_request(request, user)
```

---

### 4.2 Access Control List (ACL)

각 데이터 객체에 대한 **접근 권한을 명시적으로 정의**합니다.

```python
# system/backend/models/acl.py

class AccessControlList:
    """데이터 객체별 접근 제어 목록"""
    
    def __init__(self, resource_type: str, resource_id: str):
        self.resource_type = resource_type
        self.resource_id = resource_id
        self.acl_entries = self._load_acl()
    
    def _load_acl(self) -> list:
        """ACL 로드"""
        
        return db.query(ACLEntry).filter(
            ACLEntry.resource_type == self.resource_type,
            ACLEntry.resource_id == self.resource_id
        ).all()
    
    def check_permission(self, user: User, permission: str) -> bool:
        """권한 확인"""
        
        for entry in self.acl_entries:
            if entry.principal_id == user.id:
                return permission in entry.permissions
        
        return False
    
    def grant_permission(self, user_id: str, permissions: list):
        """권한 부여"""
        
        acl_entry = ACLEntry(
            resource_type=self.resource_type,
            resource_id=self.resource_id,
            principal_id=user_id,
            permissions=permissions,
            granted_by=current_user.id,
            granted_at=datetime.utcnow()
        )
        
        db.session.add(acl_entry)
        db.session.commit()


# 사용 예시
student_acl = AccessControlList("student", student_id="12345")

# 학부모에게 읽기 권한 부여
student_acl.grant_permission(
    user_id=parent_id,
    permissions=["read", "read_learning_data"]
)

# 교사에게 읽기/쓰기 권한 부여
student_acl.grant_permission(
    user_id=teacher_id,
    permissions=["read", "write", "read_learning_data", "write_grades"]
)
```

---

### 4.3 Role-Based Access Control (RBAC)

사용자에게 역할을 부여하고, **역할에 따라 API 및 데이터 접근 권한을 제어**합니다.

```yaml
# governance/policies/rbac_policy.yaml

rbac_configuration:
  roles:
    platform_admin:
      description: "플랫폼 최고 관리자"
      permissions:
        - "manage_all_users"
        - "manage_system_settings"
        - "view_all_data"
        - "manage_policies"
        - "emergency_access_pii"  # 긴급 시 승인 필요
        
    school_admin:
      description: "학교 관리자"
      permissions:
        - "manage_school_users"
        - "view_school_data"
        - "manage_school_settings"
      constraints:
        - "school_id must match"
        
    teacher:
      description: "교사"
      permissions:
        - "view_class_data"
        - "manage_assignments"
        - "approve_ai_content"
        - "write_grades"
        - "write_teacher_notes"
      constraints:
        - "class_id must match"
        
    parent:
      description: "학부모"
      permissions:
        - "view_child_data"
        - "manage_child_consent"
        - "request_data_deletion"
      constraints:
        - "child_id must match"
        
    student:
      description: "학생"
      permissions:
        - "view_own_data"
        - "use_ai_tutor"
        - "submit_assignments"
        - "provide_feedback"
      constraints:
        - "student_id must be self"
```

---

## 결론

DreamSeedAI는 **명확하게 정의된 역할과 책임 구조**를 통해:

1. **플랫폼의 안전하고 효율적인 운영 보장**
2. **각 이해관계자의 권리 보호**
3. **책임 소재 명확화**
4. **사용자 신뢰 구축**

을 실현합니다.

### 핵심 원칙

- **최소 권한 원칙 (Principle of Least Privilege)**: 필요한 최소한의 권한만 부여
- **직무 분리 (Separation of Duties)**: 중요한 작업은 여러 역할의 협력 필요
- **투명성 (Transparency)**: 모든 접근 및 작업 기록
- **책임성 (Accountability)**: 모든 작업에 책임자 명확히 지정

---

## 참조 문서

- [거버넌스 계층 운영](./GOVERNANCE_LAYER_OPERATIONS.md)
- [거버넌스 계층 상세 설계](./GOVERNANCE_LAYER_DETAILED.md)
- [4계층 아키텍처](./4_LAYER_ARCHITECTURE.md)

---

**문서 버전**: 1.0.0  
**최종 업데이트**: 2025-11-07  
**작성자**: DreamSeedAI Security & Governance Team  
**승인**: DreamSeedAI 운영 위원회
