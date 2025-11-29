# 🏙️ DreamSeedAI MegaCity – Policy Engine Architecture

## 통합 정책 · 규제 · 승인 · 감사 시스템

**버전:** 1.0  
**작성일:** 2025-11-20  
**작성자:** DreamSeedAI Architecture Team

---

# 📌 0. 개요

DreamSeedAI MegaCity Policy Engine은 모든 Zone(9개 도메인)과 Tenant(학교/학원/기관) 전반에서
**일관된 정책(Rules), 승인(Approvals), 감사(Audit), 접근 제어(Access Control)** 를 제공하는 중앙 규제 시스템입니다.

MegaCity의 모든 서비스는 Policy Engine을 통해 다음을 보장합니다:

* 보안 정책 (시험 중 AI 차단)
* 역할 기반 정책 (RBAC)
* 조건 기반 정책 (PBAC)
* Parent / Student 승인 흐름
* Teacher / Org Admin 승인 흐름
* Zone/Tenant 간 접근 제한
* Audit Log 자동 기록

---

# 🧩 1. Policy Engine의 5대 핵심 구성요소

```
Policy Engine
 ├── Authentication Policies (SSO / Session / MFA)
 ├── Authorization Policies (RBAC / PBAC)
 ├── Access Policies (Zone / Tenant / Data)
 ├── Approval Policies (Parent/Teacher/Org)
 └── Audit Policies (Logging, Monitoring)
```

---

# 🔐 2. Authentication Policies

**DreamSeed Global ID 기반 인증 정책**

## 2.1 Token 정책

* Access Token (15분)
* Refresh Token (14일)
* Token Rotation
* Multi-domain Cookie `.dreamseedai.com`

## 2.2 보안 강화

* MFA/TOTP 지원
* Suspicious Login Detection
* IP-based Rate Limiting
* Device Fingerprinting

## 2.3 구현 예시

```python
@app.middleware("http")
async def auth_policy_middleware(request: Request, call_next):
    token = request.cookies.get("access_token")
    if not token:
        return JSONResponse(status_code=401, content={"error": "Unauthorized"})
    
    user = verify_token(token)
    if not user:
        return JSONResponse(status_code=401, content={"error": "Invalid token"})
    
    request.state.user = user
    return await call_next(request)
```

---

# 🧑‍💻 3. Authorization Policies (RBAC)

## 3.1 기본 역할

```
student, parent, teacher, tutor,
org_admin, zone_admin, sys_admin
```

## 3.2 권한 매트릭스

| Role | Exam Create | AI Tutor | Dashboard View | User Manage |
|------|-------------|----------|----------------|-------------|
| student | ❌ | ✅ | ✅ (self) | ❌ |
| parent | ❌ | ❌ | ✅ (children) | ❌ |
| teacher | ✅ | ✅ | ✅ (class) | ❌ |
| org_admin | ✅ | ✅ | ✅ (org) | ✅ |
| sys_admin | ✅ | ✅ | ✅ (all) | ✅ |

## 3.3 구현 예시

각 역할별 권한 목록을 중앙에서 관리하며, FastAPI에서 **require_permission()** 을 통해 평가합니다.

```python
def require_permission(permission: str):
    async def check_permission(request: Request):
        user = request.state.user
        if not has_permission(user.role, permission):
            raise HTTPException(status_code=403, detail="Forbidden")
        return user
    return Depends(check_permission)

@app.post("/api/v1/exams")
async def create_exam(
    user: User = require_permission("exam:create")
):
    # Exam creation logic
    pass
```

---

# 🔍 4. Conditional Policies (PBAC)

조건 기반 정책을 통한 세밀한 접근 제어:

## 4.1 시험 중 AI 차단 정책

```python
IF user.role == 'student' AND exam.in_progress == True
THEN deny(ai_tutor_access)
```

## 4.2 로케일 기반 모델 선택 정책

```python
IF user.locale == 'kr'
THEN prefer_model = 'Seoul-Medium-KR'
ELIF user.locale == 'en'
THEN prefer_model = 'GPT-4.2-Mini'
```

## 4.3 Zone 기반 기능 제한 정책

```python
IF zone_id == 'kzone' AND feature == 'voice_analysis'
THEN require_subscription = 'ktube-pro'
```

## 4.4 구현 예시

```python
class PolicyEngine:
    def evaluate(self, user: User, resource: str, action: str) -> bool:
        # Exam in progress check
        if action == "ai_tutor:access":
            exam_session = get_active_exam_session(user.id)
            if exam_session and exam_session.status == "in_progress":
                return False
        
        # RBAC check
        return has_permission(user.role, f"{resource}:{action}")
```

---

# 🏫 5. Approval Policies

## 5.1 Parent → Student 승인 흐름

```
1. Parent 요청: POST /api/v1/approvals/parent-student
2. Student 승인: POST /api/v1/approvals/{id}/approve
3. 관계 생성: parent_student_links 테이블
4. 접근 권한: parent는 child 데이터 조회 가능
```

## 5.2 Teacher → Class / Student 승인

```
1. Teacher 등록: org_admin 승인 필요
2. Class 생성: org_admin 권한 체크
3. Student 배정: class 소유권 확인
```

## 5.3 Approval Workflow 구현

```python
@app.post("/api/v1/approvals/parent-student")
async def request_parent_student_link(
    student_code: str,
    user: User = Depends(get_current_user)
):
    if user.role != "parent":
        raise HTTPException(403, "Only parents can request")
    
    student = get_student_by_code(student_code)
    approval = create_approval_request(
        type="parent_student",
        requester_id=user.id,
        target_id=student.id,
        status="pending"
    )
    
    # Send notification to student
    notify_student(student.id, approval.id)
    return approval

@app.post("/api/v1/approvals/{id}/approve")
async def approve_request(
    id: int,
    user: User = Depends(get_current_user)
):
    approval = get_approval(id)
    if approval.target_id != user.id:
        raise HTTPException(403, "Not authorized")
    
    approval.status = "approved"
    create_parent_student_link(
        parent_id=approval.requester_id,
        student_id=approval.target_id
    )
    return approval
```

---

# 🧱 6. Access Policies (Zone/Tenant)

## 6.1 Zone-level 제한

```python
req.hostname → zone_id
```

Zone mismatch인 경우 요청 차단.

```python
@app.middleware("http")
async def zone_isolation_middleware(request: Request, call_next):
    hostname = request.headers.get("host")
    zone_id = extract_zone_from_hostname(hostname)
    
    request.state.zone_id = zone_id
    return await call_next(request)
```

## 6.2 Tenant-level 제한(org_id)

다른 학교/기관 데이터 접근 불가.
DB RLS(Row Level Security)로 강제.

```python
@app.middleware("http")
async def tenant_isolation_middleware(request: Request, call_next):
    user = request.state.user
    db.execute(f"SET app.current_org_id = {user.org_id}")
    db.execute(f"SET app.current_zone_id = '{user.zone_id}'")
    return await call_next(request)
```

---

# 📜 7. Audit Policies

모든 이벤트 자동 기록:

## 7.1 Audit Log 대상

* login/logout
* exam start/end
* policy violation
* ai_tutor usage
* parent-student approvals
* admin actions
* data export/delete requests

## 7.2 Audit Log 스키마

```sql
CREATE TABLE audit_log (
  id SERIAL PRIMARY KEY,
  zone_id VARCHAR NOT NULL,
  org_id INTEGER NOT NULL,
  user_id INTEGER NOT NULL,
  action VARCHAR(100) NOT NULL,
  resource VARCHAR(100),
  resource_id INTEGER,
  ip_address VARCHAR(50),
  user_agent TEXT,
  metadata JSONB,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_audit_log_user ON audit_log(user_id, created_at);
CREATE INDEX idx_audit_log_action ON audit_log(action, created_at);
```

## 7.3 Audit Log 구현

```python
async def log_audit(
    user: User,
    action: str,
    resource: str = None,
    resource_id: int = None,
    metadata: dict = None
):
    audit = AuditLog(
        zone_id=user.zone_id,
        org_id=user.org_id,
        user_id=user.id,
        action=action,
        resource=resource,
        resource_id=resource_id,
        metadata=metadata,
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent")
    )
    db.add(audit)
    await db.commit()
```

---

# ⚙️ 8. Policy Engine Technical Stack

## 8.1 구성 요소

* **FastAPI Dependency System**: 권한 체크 데코레이터
* **Redis**: Policy Cache (TTL 5분)
* **PostgreSQL**: Policy Store (영구 저장)
* **Cloudflare WAF Rules**: Edge-level 정책
* **Nginx/Traefik Rate Limit**: Application-level 정책
* **Pydantic v2**: Policy Models 검증
* **Internal Policy DSL**: 향후 확장 (Python-based DSL)

## 8.2 Policy Cache 전략

```python
async def get_user_permissions(user_id: int) -> list[str]:
    cache_key = f"permissions:{user_id}"
    cached = await redis.get(cache_key)
    
    if cached:
        return json.loads(cached)
    
    permissions = db.query(Permission).filter(
        Permission.role == user.role
    ).all()
    
    await redis.setex(cache_key, 300, json.dumps(permissions))
    return permissions
```

---

# 🧪 9. 정책 테스트 전략 (Policy Testing)

## 9.1 Static Tests (정적 정책 확인)

```python
def test_rbac_matrix():
    assert has_permission("student", "exam:create") == False
    assert has_permission("teacher", "exam:create") == True
    assert has_permission("parent", "dashboard:view") == True
```

## 9.2 Dynamic Tests (Request-based 정책 평가)

```python
@pytest.mark.asyncio
async def test_ai_tutor_blocked_during_exam():
    user = create_test_student()
    exam_session = create_active_exam(user.id)
    
    response = await client.post("/api/v1/ai-tutor", auth=user.token)
    assert response.status_code == 403
    assert "exam in progress" in response.json()["detail"]
```

## 9.3 Scenario-based Tests

* Exam 시작 → AI Tutor 차단 확인
* Parent 승인 → Child Dashboard 접근 확인
* Zone 이동 → org_id 격리 확인

## 9.4 Multi-zone Cross-access 테스트

```python
@pytest.mark.asyncio
async def test_cross_zone_isolation():
    user_univprep = create_user(zone_id="100", org_id=1000)
    user_skillprep = create_user(zone_id="300", org_id=3000)
    
    # UnivPrep user cannot access SkillPrep data
    response = await client.get(
        "/api/v1/exams?org_id=3000",
        auth=user_univprep.token
    )
    assert response.status_code == 403
```

---

# 🚦 10. Architecture Diagram

```
┌─────────┐
│ Request │
└────┬────┘
     │
     ▼
┌─────────────┐
│    Auth     │ ← Access Token / Refresh Token
└────┬────────┘
     │
     ▼
┌──────────────────┐
│  Policy Engine   │ ← RBAC / PBAC Rules
└────┬─────────────┘
     │
     ├─→ RBAC Check (Role-based)
     ├─→ PBAC Check (Condition-based)
     ├─→ Access Check (Zone/Tenant)
     └─→ Approval Check (Parent/Teacher)
     │
     ▼
┌─────────────┐
│    Audit    │ ← Log all actions
└────┬────────┘
     │
     ▼
┌──────────┐
│ Response │
└──────────┘
```

---

# 🔒 11. Security Best Practices

## 11.1 정책 업데이트 프로세스

1. Policy 변경 제안
2. 코드 리뷰
3. 테스트 환경 배포
4. 정책 검증 (테스트)
5. 프로덕션 배포
6. Audit Log 모니터링

## 11.2 정책 위반 시 대응

* Immediate Alert (Critical violations)
* Automatic Block (Suspicious activity)
* Manual Review (Admin intervention)

## 11.3 GDPR/PIPA 준수

* 데이터 접근 로그 1년 보관
* 데이터 삭제 요청 30일 이내 처리
* 데이터 Export 기능 제공

---

# 🏁 12. 결론

이 문서는 MegaCity 전체의 **'규제기관'** 역할을 수행하는 정책 엔진의 표준 구조를 정의합니다.

정책 적용은 Multi-zone / Multi-tenant 도시에서 일관성과 보안을 유지하는 핵심 요소입니다.

핵심 원칙:

1. **모든 요청은 Policy Engine을 통과**
2. **Zero Trust**: 모든 접근은 검증 필요
3. **Audit Everything**: 모든 행동은 기록
4. **Fail Secure**: 정책 평가 실패 시 차단
5. **Policy as Code**: 정책은 코드로 관리

---

**문서 완료 - DreamSeedAI MegaCity Policy Engine Architecture v1.0**
