# DreamSeedAI 통합 인증 시스템

## 개요

**Doc 02 - 인증, 권한, 멀티테넌시 설계**를 완전히 준수하는 통합 인증 시스템입니다.

### 핵심 기능

✅ **하이브리드 인증**
- JWT 토큰 인증 (API 클라이언트, 모바일 앱)
- OIDC 헤더 기반 인증 (웹 대시보드, 역방향 프록시)
- 개발 모드 (`LOCAL_DEV=true`)

✅ **역할 기반 접근 제어 (RBAC)**
- 5가지 표준 역할: admin, teacher, counselor, student, viewer
- 역할 정규화 (canonicalization): 다양한 IdP 역할 이름 자동 변환
- 세밀한 권한 제어: 엔드포인트, 함수, 리소스 레벨

✅ **멀티테넌시 데이터 격리**
- 조직(org_id) 기반 자동 필터링
- SQLAlchemy 및 Raw SQL 지원
- Admin 권한 우회 기능
- 세션/리소스 접근 제어

## 파일 구조

```
apps/seedtest_api/auth/
├── unified.py          # 🌟 통합 인증 모듈 (메인)
├── multitenancy.py     # 🌟 멀티테넌시 데이터 격리
├── deps.py             # JWT 인증 (새 버전, UserContext 사용)
├── header_auth.py      # OIDC 헤더 인증 (레거시, unified.py로 통합됨)
└── README.md           # 이 파일
```

### 주요 모듈

#### 1. `unified.py` - 통합 인증 모듈

**모든 인증 기능의 단일 진입점**

```python
from apps.seedtest_api.auth.unified import (
    # 인증
    get_current_user,           # 메인 인증 함수 (JWT + Header 하이브리드)
    UserContext,                # 사용자 컨텍스트 모델
    
    # 역할 기반 접근 제어
    require_role,               # 특정 역할 필요
    require_admin,              # Admin만
    require_teacher_or_admin,   # Teacher 또는 Admin
    
    # 유틸리티
    canonicalize_roles,         # 역할 정규화
)
```

**주요 기능:**
- JWT 토큰 디코딩 (HS256, RS256 지원)
- OIDC 헤더 파싱
- 역할 정규화 (한국어, 영어 키워드 지원)
- 개발 모드 지원
- 레거시 호환성 (`User` 모델)

#### 2. `multitenancy.py` - 멀티테넌시 모듈

**조직 기반 데이터 격리**

```python
from apps.seedtest_api.auth.multitenancy import (
    # SQLAlchemy 필터
    enforce_org_filter,         # WHERE 절 생성
    get_org_filter_value,       # org_id 값 반환
    
    # Raw SQL 헬퍼
    get_org_filter_sql,         # SQL WHERE 절 문자열
    
    # 접근 제어
    verify_org_access,          # 리소스 조직 검증
    verify_session_access,      # 세션 접근 검증
    verify_org_match,           # 두 조직 ID 일치 확인
    
    # 벌크 작업
    filter_by_org,              # 리스트 필터링
    validate_org_ids,           # 여러 org_id 검증
)
```

**주요 기능:**
- SQLAlchemy 쿼리 자동 필터링
- Raw SQL 안전한 org_id 필터링
- 세션/리소스 접근 규칙 (Admin/Teacher/Student)
- 벌크 작업 검증

## 빠른 시작

### 1. 기본 인증

```python
from fastapi import APIRouter, Depends
from apps.seedtest_api.auth.unified import get_current_user, UserContext

router = APIRouter()

@router.get("/me")
async def get_me(user: UserContext = Depends(get_current_user)):
    return {
        "user_id": user.user_id,
        "org_id": user.org_id,
        "roles": user.roles,
    }
```

### 2. 역할 기반 접근 제어

```python
from apps.seedtest_api.auth.unified import require_role

@router.get("/admin", dependencies=[Depends(require_role("admin"))])
async def admin_panel(user: UserContext = Depends(get_current_user)):
    return {"message": "Admin only"}
```

### 3. 멀티테넌시 데이터 격리

```python
from sqlalchemy import select
from apps.seedtest_api.auth.multitenancy import enforce_org_filter
from models import Student

@router.get("/students")
async def list_students(
    user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 자동으로 user의 조직만 필터링 (Admin은 모든 조직 조회)
    stmt = select(Student).where(enforce_org_filter(Student.org_id, user))
    students = db.execute(stmt).scalars().all()
    return students
```

## 역할 (Roles)

### 표준 역할

| 역할 | 설명 | 권한 |
|------|------|------|
| `admin` | 시스템 관리자 | 모든 조직 접근, 모든 기능 |
| `teacher` | 교사 | 자신의 조직 내 학급 관리, 학생 평가 |
| `counselor` | 상담 교사 | 자신의 조직 내 학생 상담, 지원 |
| `student` | 학생 | 자신의 데이터만 접근 |
| `viewer` | 조회 전용 | 읽기 권한만 (기본 역할) |

### 역할 정규화

다양한 IdP의 역할 이름을 자동으로 표준 역할로 변환:

```python
canonicalize_roles("Admin, Principal")      # → ["admin"]
canonicalize_roles("Teacher, 교사")         # → ["teacher"]
canonicalize_roles("상담사, Counselor")     # → ["counselor"]
canonicalize_roles("Student, 학생")         # → ["student"]
```

**지원 키워드:**
- **Admin**: admin, 관리자, administrator, principal, 교장
- **Teacher**: teacher, 교사, 선생, instructor, professor
- **Counselor**: counsel, 상담, advisor, guidance
- **Student**: student, 학생, pupil, learner
- **Viewer**: viewer, 조회, reader, guest, 일반

## 인증 방식

### 1. JWT 토큰 (API 클라이언트)

```bash
curl http://localhost:8000/api/students \
  -H "Authorization: Bearer eyJ..."
```

**JWT Payload:**
```json
{
  "sub": "user123",
  "org_id": "org456",
  "roles": ["teacher"],
  "scope": "dashboard:read"
}
```

### 2. OIDC 헤더 (웹 대시보드)

```bash
curl http://localhost:8000/api/students \
  -H "X-User: user123" \
  -H "X-Org-Id: org456" \
  -H "X-Roles: teacher, admin"
```

### 3. 개발 모드

```bash
export LOCAL_DEV=true
curl http://localhost:8000/api/students  # 인증 없이 접근 가능
```

## 환경 변수

```bash
# JWT 설정
JWT_SECRET=your-secret-key
JWT_ALGORITHM=HS256  # 또는 RS256
JWT_PUBLIC_KEY=-----BEGIN PUBLIC KEY-----...  # RS256용

# OIDC 헤더 설정
AUTH_HEADER_USER=X-User
AUTH_HEADER_ORG=X-Org-Id
AUTH_HEADER_ROLES=X-Roles

# 개발 모드
LOCAL_DEV=false  # 프로덕션에서는 반드시 false
```

## 마이그레이션 가이드

### 레거시 코드

```python
# 기존 deps.py 사용
from ..deps import User, get_current_user, require_session_access

@router.get("/endpoint")
async def endpoint(
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_session_access),
):
    ...
```

### 새 코드 (통합 인증)

```python
# 통합 인증 사용
from apps.seedtest_api.auth.unified import get_current_user, UserContext
from apps.seedtest_api.auth.multitenancy import verify_session_access

@router.get("/endpoint")
async def endpoint(
    user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 세션 조회
    session = db.query(ExamSession).filter(...).first()
    
    # 접근 권한 검증
    verify_session_access(session.user_id, session.org_id, user)
    ...
```

### 체크리스트

- [ ] `User` → `UserContext`
- [ ] `current_user` → `user` (컨벤션)
- [ ] `require_session_access` → `verify_session_access`
- [ ] DB 쿼리에 `enforce_org_filter()` 추가
- [ ] 역할 확인 메서드 업데이트 (정규화된 역할 사용)

## 예제

전체 예제는 다음 파일 참조:
- **예제 라우터**: `/apps/seedtest_api/routers/example_unified_auth.py`
- **구현 가이드**: `/docs/AUTH_IMPLEMENTATION_GUIDE.md`

## 보안 고려사항

### ⚠️ 중요: 역방향 프록시 설정

프록시는 **반드시** 외부 요청의 모든 `X-*` 헤더를 제거해야 합니다.

**nginx 예시:**
```nginx
location /api/ {
    # 외부 헤더 제거
    proxy_set_header X-User "";
    proxy_set_header X-Org-Id "";
    proxy_set_header X-Roles "";
    
    # oauth2-proxy가 설정한 헤더만 전달
    auth_request /oauth2/auth;
    ...
}
```

### 프로덕션 체크리스트

- [ ] `LOCAL_DEV=false` 설정
- [ ] JWT_SECRET 강력한 값으로 설정
- [ ] 역방향 프록시에서 외부 헤더 제거 확인
- [ ] HTTPS 사용
- [ ] 토큰 만료 시간 적절히 설정

## 문서

- **구현 가이드**: `/docs/AUTH_IMPLEMENTATION_GUIDE.md` (상세 가이드)
- **Doc 02**: `/docs/Doc02_Auth_Permissions_MultiTenancy.md` (설계 문서)
- **예제 라우터**: `/apps/seedtest_api/routers/example_unified_auth.py`

## API 레퍼런스

### UserContext

```python
class UserContext:
    user_id: str                    # 사용자 ID
    org_id: Optional[str]           # 조직 ID
    roles: list[str]                # 정규화된 역할
    scope: Optional[str]            # OAuth2 scope
    auth_method: str                # jwt, header, dev
    
    # 메서드
    def is_admin(self) -> bool
    def is_teacher(self) -> bool
    def is_counselor(self) -> bool
    def is_student(self) -> bool
    def is_viewer(self) -> bool
    def has_role(self, *roles: str) -> bool
```

### 주요 함수

```python
# 인증
async def get_current_user(...) -> UserContext
def require_role(*allowed) -> Callable
def require_admin(user) -> UserContext
def require_teacher_or_admin(user) -> UserContext

# 역할 정규화
def canonicalize_roles(raw_roles: str | list[str]) -> list[str]

# 멀티테넌시
def enforce_org_filter(org_id_column, user, allow_null=False) -> ColumnElement
def get_org_filter_sql(org_id_column: str, user, allow_null=False) -> str
def verify_org_access(resource_org_id, user, resource_name="resource") -> None
def verify_session_access(session_user_id, session_org_id, user) -> None
```

## 변경 이력

- **2025-11-07**: 초기 구현
  - `unified.py`: 통합 인증 모듈
  - `multitenancy.py`: 멀티테넌시 데이터 격리
  - Doc 02 완전 준수
  - JWT + Header 하이브리드 인증
  - 역할 정규화 (한국어/영어 지원)
