# DreamSeedAI 통합 인증 시스템 구현 가이드

## 개요

본 문서는 **Doc 02 - 인증, 권한, 멀티테넌시 설계**를 기반으로 구현된 통합 인증 시스템의 사용 가이드입니다.

### 주요 특징

✅ **Doc 02 완전 준수**
- OIDC 역방향 프록시 헤더 기반 인증
- JWT 토큰 인증 (API 클라이언트용)
- 역할 기반 접근 제어 (RBAC)
- 조직 기반 멀티테넌시

✅ **하이브리드 인증**
- JWT와 헤더 인증을 동시 지원
- 개발 모드 (`LOCAL_DEV`) 지원
- 기존 코드와 호환성 유지

✅ **강력한 데이터 격리**
- 조직(org_id) 기반 자동 필터링
- SQLAlchemy 및 Raw SQL 지원
- Admin 권한 우회 기능

## 파일 구조

```
apps/seedtest_api/auth/
├── unified.py          # 통합 인증 모듈 (메인)
├── multitenancy.py     # 멀티테넌시 데이터 격리
├── deps.py             # JWT 인증 (새 버전)
├── header_auth.py      # OIDC 헤더 인증 (레거시)
└── __init__.py

apps/seedtest_api/
├── deps.py             # 레거시 인증 (마이그레이션 필요)
└── routers/
    ├── analysis.py     # 마이그레이션 필요
    ├── exams.py        # 마이그레이션 필요
    └── ...
```

## 빠른 시작

### 1. 기본 사용법

```python
from fastapi import APIRouter, Depends
from apps.seedtest_api.auth.unified import (
    get_current_user,
    require_role,
    UserContext
)

router = APIRouter()

@router.get("/dashboard")
async def get_dashboard(user: UserContext = Depends(get_current_user)):
    """모든 인증된 사용자 접근 가능"""
    return {
        "user_id": user.user_id,
        "org_id": user.org_id,
        "roles": user.roles
    }

@router.get("/admin", dependencies=[Depends(require_role("admin"))])
async def admin_panel(user: UserContext = Depends(get_current_user)):
    """Admin만 접근 가능"""
    return {"message": "Admin panel"}

@router.post("/classes", dependencies=[Depends(require_role("teacher", "admin"))])
async def create_class(user: UserContext = Depends(get_current_user)):
    """Teacher 또는 Admin만 접근 가능"""
    return {"message": "Class created"}
```

### 2. 멀티테넌시 데이터 격리

```python
from sqlalchemy import select
from apps.seedtest_api.auth.unified import get_current_user, UserContext
from apps.seedtest_api.auth.multitenancy import (
    enforce_org_filter,
    verify_org_access,
    get_org_filter_sql
)
from models import Student

@router.get("/students")
async def list_students(
    user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """사용자 조직의 학생만 조회"""
    # SQLAlchemy 방식
    stmt = select(Student).where(
        enforce_org_filter(Student.org_id, user)
    )
    students = db.execute(stmt).scalars().all()
    return students

@router.get("/students/{student_id}")
async def get_student(
    student_id: str,
    user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """특정 학생 조회 (조직 검증)"""
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(404, "Student not found")
    
    # 조직 접근 권한 검증
    verify_org_access(student.org_id, user, "student")
    
    return student
```

### 3. Raw SQL 사용

```python
from apps.seedtest_api.auth.multitenancy import get_org_filter_sql

@router.get("/reports")
async def get_reports(user: UserContext = Depends(get_current_user)):
    """Raw SQL로 조직 필터링"""
    org_filter = get_org_filter_sql("org_id", user)
    
    sql = f"""
        SELECT * FROM exam_sessions
        WHERE {org_filter}
        ORDER BY created_at DESC
    """
    
    results = db.execute(sql).fetchall()
    return results
```

## 인증 방식

### 1. JWT 토큰 인증 (API 클라이언트)

```bash
# 토큰 발급
curl -X POST http://localhost:8000/api/auth/token \
  -H "Authorization: Bearer <existing-token>"

# API 호출
curl http://localhost:8000/api/students \
  -H "Authorization: Bearer <jwt-token>"
```

**JWT Payload 예시:**
```json
{
  "sub": "user123",
  "user_id": "user123",
  "org_id": "org456",
  "tenant_id": "org456",
  "roles": ["teacher", "admin"],
  "scope": "dashboard:read dashboard:write",
  "iss": "dreamseedai",
  "aud": "dashboard",
  "iat": 1699000000,
  "exp": 1699014400
}
```

### 2. OIDC 헤더 인증 (웹 대시보드)

역방향 프록시(oauth2-proxy, Keycloak 등)가 설정한 헤더 사용:

```http
GET /api/students HTTP/1.1
X-User: user123
X-Org-Id: org456
X-Roles: teacher, admin
```

**환경 변수로 헤더 이름 커스터마이징:**
```bash
export AUTH_HEADER_USER=X-Forwarded-User
export AUTH_HEADER_ORG=X-Forwarded-Org
export AUTH_HEADER_ROLES=X-Forwarded-Roles
```

### 3. 개발 모드 (LOCAL_DEV)

```bash
export LOCAL_DEV=true

# 인증 없이 API 호출 가능
curl http://localhost:8000/api/students
```

**개발 모드 사용자:**
```python
UserContext(
    user_id="dev-user",
    org_id="1",
    roles=["admin", "teacher", "student"],
    scope="*",
    auth_method="dev"
)
```

## 역할 (Roles)

### 표준 역할

| 역할 | 설명 | 권한 |
|------|------|------|
| `admin` | 시스템 관리자 | 모든 조직 접근, 모든 기능 사용 |
| `teacher` | 교사 | 자신의 조직 내 학급 관리, 학생 평가 |
| `counselor` | 상담 교사 | 자신의 조직 내 학생 상담, 지원 |
| `student` | 학생 | 자신의 데이터만 접근 |
| `viewer` | 조회 전용 | 읽기 권한만 (기본 역할) |

### 역할 정규화 (Canonicalization)

다양한 IdP의 역할 이름을 표준 역할로 자동 변환:

```python
canonicalize_roles("  Admin,  Principal")  # → ["admin"]
canonicalize_roles("Teacher, 교사")         # → ["teacher"]
canonicalize_roles("상담사, Counselor")     # → ["counselor"]
canonicalize_roles("Student, 학생")         # → ["student"]
canonicalize_roles("일반 사용자")            # → ["viewer"]
```

**지원 키워드:**
- **Admin**: admin, 관리자, administrator, principal, 교장
- **Teacher**: teacher, 교사, 선생, instructor, professor
- **Counselor**: counsel, 상담, advisor, guidance
- **Student**: student, 학생, pupil, learner
- **Viewer**: viewer, 조회, reader, guest, 일반

## UserContext API

```python
class UserContext:
    user_id: str                    # 사용자 고유 ID
    org_id: Optional[str]           # 조직 ID
    roles: list[str]                # 정규화된 역할 목록
    scope: Optional[str]            # OAuth2 scope
    auth_method: str                # 인증 방식 (jwt, header, dev)
    
    # 속성
    @property
    def tenant_id(self) -> Optional[str]  # org_id 별칭
    
    # 역할 확인 메서드
    def is_admin(self) -> bool
    def is_teacher(self) -> bool
    def is_counselor(self) -> bool
    def is_student(self) -> bool
    def is_viewer(self) -> bool
    def has_role(self, *roles: str) -> bool
```

## 접근 제어 패턴

### 1. 엔드포인트 레벨 제어

```python
from apps.seedtest_api.auth.unified import require_role, require_admin

# 특정 역할 필요
@router.get("/classes", dependencies=[Depends(require_role("teacher", "admin"))])
async def list_classes(): ...

# Admin만
@router.delete("/users/{user_id}", dependencies=[Depends(require_admin)])
async def delete_user(): ...
```

### 2. 함수 내부 제어

```python
@router.post("/assignments")
async def create_assignment(user: UserContext = Depends(get_current_user)):
    if not user.has_role("teacher", "admin"):
        raise HTTPException(403, "Teacher or admin role required")
    
    # 로직 계속...
```

### 3. 세션/리소스 접근 제어

```python
from apps.seedtest_api.auth.multitenancy import verify_session_access

@router.get("/exams/{session_id}")
async def get_exam(
    session_id: str,
    user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 세션 조회
    session = db.query(ExamSession).filter(id=session_id).first()
    if not session:
        raise HTTPException(404, "Session not found")
    
    # 접근 권한 검증
    # - Admin: 모든 세션 접근 가능
    # - Teacher: 같은 조직의 세션만
    # - Student: 자신의 세션만
    verify_session_access(session.user_id, session.org_id, user)
    
    return session
```

## 마이그레이션 가이드

### 기존 코드 (레거시)

```python
# 기존 deps.py 사용
from ..deps import User, get_current_user, require_session_access

@router.get("/analysis/{session_id}")
async def get_analysis(
    session_id: str,
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_session_access),
):
    # ...
```

### 새 코드 (통합 인증)

```python
# 통합 인증 사용
from apps.seedtest_api.auth.unified import get_current_user, UserContext
from apps.seedtest_api.auth.multitenancy import verify_session_access

@router.get("/analysis/{session_id}")
async def get_analysis(
    session_id: str,
    user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 세션 조회
    session = db.query(ExamSession).filter(id=session_id).first()
    if not session:
        raise HTTPException(404, "Session not found")
    
    # 접근 권한 검증 (Admin/Teacher/Student 규칙 자동 적용)
    verify_session_access(session.user_id, session.org_id, user)
    
    # 분석 로직...
```

### 마이그레이션 체크리스트

- [ ] `from ..deps import User` → `from apps.seedtest_api.auth.unified import UserContext`
- [ ] `from ..deps import get_current_user` → `from apps.seedtest_api.auth.unified import get_current_user`
- [ ] `User` 타입 → `UserContext` 타입
- [ ] `require_session_access` → `verify_session_access` (multitenancy 모듈)
- [ ] DB 쿼리에 `enforce_org_filter()` 추가
- [ ] 역할 확인: `user.is_admin()` → `user.is_admin()` (동일, 하지만 정규화된 역할 사용)

## 환경 변수

```bash
# JWT 설정
JWT_SECRET=your-secret-key-change-in-production
JWT_ALGORITHM=HS256  # 또는 RS256
JWT_PUBLIC_KEY=-----BEGIN PUBLIC KEY-----...  # RS256 사용 시

# OIDC 헤더 설정 (커스터마이징 가능)
AUTH_HEADER_USER=X-User
AUTH_HEADER_ORG=X-Org-Id
AUTH_HEADER_ROLES=X-Roles
AUTH_HEADER_GROUPS=X-Auth-Request-Groups

# 개발 모드
LOCAL_DEV=false  # 프로덕션에서는 반드시 false
```

## 보안 고려사항

### 1. 역방향 프록시 설정

**중요**: 프록시는 외부 요청의 모든 `X-*` 헤더를 제거해야 합니다.

**oauth2-proxy 예시:**
```yaml
# oauth2-proxy.cfg
pass_authorization_header = true
pass_user_headers = true
set_authorization_header = true

# 외부 헤더 제거
skip_auth_strip_headers = false
```

**nginx 예시:**
```nginx
location /api/ {
    # 외부 헤더 제거
    proxy_set_header X-User "";
    proxy_set_header X-Org-Id "";
    proxy_set_header X-Roles "";
    
    # oauth2-proxy가 설정한 헤더만 전달
    auth_request /oauth2/auth;
    auth_request_set $user $upstream_http_x_auth_request_user;
    auth_request_set $org $upstream_http_x_auth_request_org;
    auth_request_set $roles $upstream_http_x_auth_request_roles;
    
    proxy_set_header X-User $user;
    proxy_set_header X-Org-Id $org;
    proxy_set_header X-Roles $roles;
    
    proxy_pass http://backend;
}
```

### 2. JWT 시크릿 관리

```bash
# 강력한 시크릿 생성
openssl rand -base64 32

# 환경 변수로 설정 (하드코딩 금지)
export JWT_SECRET=$(cat /run/secrets/jwt_secret)
```

### 3. 프로덕션 체크리스트

- [ ] `LOCAL_DEV=false` 설정
- [ ] JWT_SECRET 강력한 값으로 설정
- [ ] 역방향 프록시에서 외부 헤더 제거 확인
- [ ] HTTPS 사용
- [ ] 토큰 만료 시간 적절히 설정
- [ ] 감사 로그 활성화

## 테스트

### 단위 테스트

```python
import pytest
from apps.seedtest_api.auth.unified import canonicalize_roles, UserContext

def test_canonicalize_roles():
    assert canonicalize_roles("Admin, Principal") == ["admin"]
    assert canonicalize_roles("Teacher, 교사") == ["teacher"]
    assert canonicalize_roles("") == ["viewer"]

def test_user_context_roles():
    user = UserContext(
        user_id="test",
        org_id="1",
        roles=["teacher", "admin"]
    )
    assert user.is_admin()
    assert user.is_teacher()
    assert not user.is_student()
    assert user.has_role("teacher", "counselor")
```

### 통합 테스트

```python
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_jwt_auth():
    # JWT 토큰으로 인증
    response = client.get(
        "/api/students",
        headers={"Authorization": "Bearer <valid-jwt>"}
    )
    assert response.status_code == 200

def test_header_auth():
    # 헤더로 인증
    response = client.get(
        "/api/students",
        headers={
            "X-User": "user123",
            "X-Org-Id": "org456",
            "X-Roles": "teacher"
        }
    )
    assert response.status_code == 200

def test_unauthorized():
    # 인증 없이 접근
    response = client.get("/api/students")
    assert response.status_code == 401
```

## 문제 해결

### Q: "Missing authentication header: X-User" 오류

**A**: OIDC 역방향 프록시가 헤더를 전달하지 않고 있습니다.
- 프록시 설정 확인
- `pass_user_headers = true` 설정 확인
- 헤더 이름이 `AUTH_HEADER_USER` 환경 변수와 일치하는지 확인

### Q: "Insufficient permissions" 오류

**A**: 사용자 역할이 부족합니다.
- JWT payload의 `roles` 필드 확인
- IdP에서 올바른 역할이 할당되었는지 확인
- `canonicalize_roles()` 함수가 역할을 올바르게 변환하는지 확인

### Q: 조직 데이터가 보이지 않음

**A**: 멀티테넌시 필터가 작동 중입니다.
- 사용자의 `org_id`와 데이터의 `org_id`가 일치하는지 확인
- Admin 역할이 필요한 경우 역할 확인
- `enforce_org_filter()` 사용 여부 확인

## 추가 리소스

- **Doc 02**: `/docs/Doc02_Auth_Permissions_MultiTenancy.md`
- **통합 인증 모듈**: `/apps/seedtest_api/auth/unified.py`
- **멀티테넌시 모듈**: `/apps/seedtest_api/auth/multitenancy.py`
- **예제 라우터**: `/apps/seedtest_api/routers/` (마이그레이션 후)

## 변경 이력

- **2025-11-07**: 초기 구현 (Doc 02 기반)
  - 통합 인증 모듈 (`unified.py`)
  - 멀티테넌시 모듈 (`multitenancy.py`)
  - JWT + Header 하이브리드 인증
  - 역할 정규화 (`canonicalize_roles`)
