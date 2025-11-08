# DreamSeedAI Governance Implementation Guide

**거버넌스 문서 → 실제 코드로 전환하는 1주 계획**

---

## 📋 개요

이 가이드는 DreamSeedAI의 거버넌스 문서를 **실제 동작하는 시스템**으로 전환하는 구체적인 실행 계획입니다.

**핵심 아이디어**: 
- 📝 **문서** → 🔧 **정책 번들 (YAML)** → 🚀 **런타임 집행 (코드)**

---

## 🎯 목표

1. **Phase 1 거버넌스 활성화** (7일 내)
   - RBAC 집행
   - 안전성 필터
   - 교사 승인 워크플로우
   - 기본 감사 로그

2. **설정 기반 제어**
   - 코드 수정 없이 환경 변수로 정책 변경
   - 거버넌스 대시보드에서 실시간 조정

3. **점진적 도입**
   - Phase 0 (soft) → Phase 1 (enforce) 전환
   - 실제 트래픽에서 검증 후 강화

---

## 📁 생성된 파일 구조

```
dreamseed_monorepo/
├── governance/                          # ✅ 생성 완료
│   ├── README.md                        # ✅
│   ├── docs/                            # ✅ (문서 이동 완료)
│   │   ├── GOVERNANCE_PHILOSOPHY.md
│   │   ├── GOVERNANCE_LAYER_OPERATIONS.md
│   │   ├── GOVERNANCE_LAYER_DETAILED.md
│   │   ├── GOVERNANCE_LAYER_SUMMARY.md
│   │   └── GOVERNANCE_ROLES_AND_RESPONSIBILITIES.md
│   ├── bundles/                         # ✅
│   │   ├── policy_bundle_phase0.yaml    # ⏳ TODO
│   │   ├── policy_bundle_phase1.yaml    # ✅
│   │   ├── policy_bundle_phase2.yaml    # ⏳ TODO
│   │   └── policy_bundle_prod.yaml      # ⏳ TODO
│   ├── compiled/                        # ✅
│   │   └── (JSON files)                 # ⏳ compile.py 실행 후 생성
│   ├── schemas/                         # ✅
│   │   └── policy-bundle.schema.json    # ✅
│   └── scripts/                         # ✅
│       ├── validate.py                  # ✅
│       ├── compile.py                   # ✅
│       └── sign.py                      # ⏳ TODO (옵션)
│
├── backend/                             # ⏳ 구현 필요
│   └── app/
│       ├── settings.py                  # ⏳ TODO: Pydantic Settings 추가
│       ├── middleware/
│       │   └── governance.py            # ⏳ TODO: GovernanceMiddleware
│       ├── policy/                      # ⏳ TODO: 정책 집행 라이브러리
│       │   ├── __init__.py
│       │   ├── loader.py                # 정책 로더
│       │   ├── rbac.py                  # RBAC 체크
│       │   ├── content_filter.py        # 콘텐츠 필터
│       │   ├── approvals.py             # 승인 워크플로우
│       │   └── feature_flags.py         # 기능 플래그
│       └── models/
│           └── governance.py            # ⏳ TODO: 감사 로그, 승인 테이블
│
└── ops/                                 # ⏳ TODO
    └── migrations/
        └── 001_governance_tables.sql    # 감사 로그, 승인 테이블
```

---

## 🚀 1주 실행 계획

### Day 1-2: 정책 번들 및 인프라

#### Day 1 오전: 정책 번들 검증

```bash
# 1. jsonschema 패키지 설치
pip install jsonschema pyyaml

# 2. Phase 1 정책 번들 검증
cd /home/won/projects/dreamseed_monorepo
python governance/scripts/validate.py governance/bundles/policy_bundle_phase1.yaml

# 3. 컴파일
python governance/scripts/compile.py governance/bundles/policy_bundle_phase1.yaml
```

**예상 출력**:
```
✅ Schema validation passed
✅ All validations passed
✅ Saved: governance/compiled/phase1.json
```

#### Day 1 오후: Phase 0, 2 정책 번들 작성

```bash
# Phase 0 (기반): 감사 로그만, 집행 안 함
cp governance/bundles/policy_bundle_phase1.yaml governance/bundles/policy_bundle_phase0.yaml
# 수정: phase: 0, enforcement.mode: soft, feature_flags 대부분 false

# Phase 2 (확장): 공정성 모니터링, org override
cp governance/bundles/policy_bundle_phase1.yaml governance/bundles/policy_bundle_phase2.yaml
# 수정: phase: 2, org_overrides.enabled: true, fairness_monitoring: true
```

#### Day 2 오전: 데이터베이스 마이그레이션

**파일 생성**: `ops/migrations/001_governance_tables.sql`

```sql
-- Approval Requests
CREATE TABLE IF NOT EXISTS approval_request (
  id SERIAL PRIMARY KEY,
  rule_id VARCHAR(64) NOT NULL,
  requester_id VARCHAR(128) NOT NULL,
  approver_role VARCHAR(64) NOT NULL,
  status VARCHAR(16) NOT NULL DEFAULT 'pending',  -- pending/approved/denied
  payload JSONB NOT NULL,
  comment TEXT,
  created_at TIMESTAMP DEFAULT NOW(),
  decided_at TIMESTAMP,
  decided_by VARCHAR(128),
  INDEX idx_status (status),
  INDEX idx_created_at (created_at)
);

-- Audit Log
CREATE TABLE IF NOT EXISTS audit_log (
  id SERIAL PRIMARY KEY,
  timestamp TIMESTAMP DEFAULT NOW(),
  org_id VARCHAR(64),
  user_id VARCHAR(128),
  action VARCHAR(128),
  policy_event VARCHAR(128),  -- e.g., RBAC_DENY, FEATURE_OFF, APPROVAL_REQUIRED
  details JSONB,
  INDEX idx_timestamp (timestamp),
  INDEX idx_policy_event (policy_event),
  INDEX idx_user_id (user_id)
);

-- Org Policy Overrides (Phase 2+)
CREATE TABLE IF NOT EXISTS org_policy_override (
  id SERIAL PRIMARY KEY,
  org_id VARCHAR(64) NOT NULL,
  bundle_id VARCHAR(64) NOT NULL,
  patch JSONB NOT NULL,
  created_at TIMESTAMP DEFAULT NOW(),
  created_by VARCHAR(128),
  UNIQUE(org_id, bundle_id)
);
```

**실행**:
```bash
# PostgreSQL에 적용
psql -U postgres -d dreamseed_db -f ops/migrations/001_governance_tables.sql
```

#### Day 2 오후: Settings 및 Policy Loader

**파일 생성**: `backend/app/settings.py` (또는 기존 파일에 추가)

```python
# backend/app/settings.py
from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    # 기존 설정...
    
    # Governance Settings
    POLICY_BUNDLE_ID: str = "phase1"
    GOVERNANCE_PHASE: int = 1
    POLICY_STRICT_MODE: str = "soft"  # soft | enforce
    ORG_POLICY_MODE: str = "deny"     # allow | deny
    POLICY_BUNDLE_PATH: str = "governance/compiled/phase1.json"
    
    class Config:
        env_file = ".env"

settings = Settings()
```

**파일 생성**: `backend/app/policy/loader.py`

```python
# backend/app/policy/loader.py
import json
from pathlib import Path
from functools import lru_cache

@lru_cache(maxsize=1)
def load_policy_bundle(path: str) -> dict:
    """Load and cache policy bundle"""
    policy_path = Path(path)
    
    if not policy_path.exists():
        raise FileNotFoundError(f"Policy bundle not found: {path}")
    
    with open(policy_path, 'r', encoding='utf-8') as f:
        bundle = json.load(f)
    
    # 필수 키 검증
    required_keys = ['bundle_id', 'phase', 'rbac', 'feature_flags']
    for key in required_keys:
        if key not in bundle:
            raise ValueError(f"Invalid policy bundle: missing '{key}'")
    
    return bundle

def reload_policy():
    """Clear cache and reload policy"""
    load_policy_bundle.cache_clear()
```

---

### Day 3-4: 정책 집행 구현

#### Day 3 오전: RBAC 모듈

**파일 생성**: `backend/app/policy/rbac.py`

```python
# backend/app/policy/rbac.py
from typing import List

def check_permission(policy: dict, roles: List[str], action: str) -> bool:
    """
    Check if any of the user's roles allow the action
    
    Args:
        policy: Policy bundle
        roles: User's roles
        action: Permission string (e.g., "student:read")
    
    Returns:
        True if allowed, False otherwise
    """
    if not policy.get('rbac', {}).get('enabled'):
        return True  # RBAC 비활성 시 모두 허용
    
    role_grants = {}
    for role in policy['rbac']['roles']:
        role_grants[role['name']] = {
            'allows': set(role.get('allows', [])),
            'denies': set(role.get('denies', []))
        }
    
    # 1. Deny 우선 (명시적 거부)
    for role in roles:
        if role not in role_grants:
            continue
        denies = role_grants[role]['denies']
        if action in denies or '*' in denies:
            return False
    
    # 2. Allow 확인
    for role in roles:
        if role not in role_grants:
            continue
        allows = role_grants[role]['allows']
        if '*' in allows or action in allows:
            return True
    
    # 3. 기본 거부
    return False


def route_to_action(method: str, path: str) -> str:
    """
    Map API route to permission action
    
    Examples:
        GET /api/v1/students/{id} -> student:read
        POST /api/v1/assignments -> assignment:create
    """
    # 간단한 매핑 로직 (실제로는 더 정교하게)
    route_map = {
        ('GET', '/api/v1/students'): 'student:read',
        ('POST', '/api/v1/assignments'): 'assignment:create',
        ('POST', '/api/v1/approvals'): 'content:approve',
        # ... 더 많은 매핑
    }
    
    return route_map.get((method, path), 'unknown:action')
```

#### Day 3 오후: Feature Flags 및 Content Filter

**파일 생성**: `backend/app/policy/feature_flags.py`

```python
# backend/app/policy/feature_flags.py

def feature_enabled(policy: dict, flag: str) -> bool:
    """Check if a feature is enabled"""
    return bool(policy.get('feature_flags', {}).get(flag, False))
```

**파일 생성**: `backend/app/policy/content_filter.py`

```python
# backend/app/policy/content_filter.py
from typing import Tuple

def check_content_safety(policy: dict, content: str) -> Tuple[bool, str]:
    """
    Check if content passes safety filters
    
    Returns:
        (is_safe, reason)
    """
    safety = policy.get('safety', {})
    if not safety.get('enabled'):
        return True, ""
    
    tutor_safety = safety.get('tutor', {})
    disallow_topics = set(tutor_safety.get('disallow_topics', []))
    
    # 간단한 키워드 필터 (실제로는 ML 모델 사용)
    content_lower = content.lower()
    for topic in disallow_topics:
        if topic.replace('-', ' ') in content_lower:
            return False, f"Contains prohibited topic: {topic}"
    
    return True, ""
```

#### Day 4 오전: Governance Middleware

**파일 생성**: `backend/app/middleware/governance.py`

```python
# backend/app/middleware/governance.py
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from ..settings import settings
from ..policy.loader import load_policy_bundle
from ..policy.rbac import check_permission, route_to_action
from ..policy.feature_flags import feature_enabled

# 정책 로드
POLICY = load_policy_bundle(settings.POLICY_BUNDLE_PATH)

class GovernanceMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 1. 사용자 컨텍스트 추출 (헤더에서)
        user_id = request.headers.get("X-User-ID", "anonymous")
        roles = request.headers.get("X-Roles", "").split(",")
        org_id = request.headers.get("X-Org-ID", "default")
        
        # 2. API 라우트 → 권한 매핑
        action = route_to_action(request.method, request.url.path)
        
        # 3. RBAC 검사
        if not check_permission(POLICY, roles, action):
            # 감사 로그 (TODO)
            return Response(
                content="Forbidden by governance policy (RBAC)",
                status_code=403
            )
        
        # 4. 기능 플래그 검사
        # 예: tutor API는 ai_tutor 플래그 필요
        if request.url.path.startswith("/api/v1/tutor"):
            if not feature_enabled(POLICY, "ai_tutor"):
                if settings.POLICY_STRICT_MODE == "enforce":
                    return Response(
                        content="Feature disabled by governance policy",
                        status_code=403
                    )
        
        # 5. 다음 단계로
        response = await call_next(request)
        return response
```

**FastAPI에 미들웨어 추가**: `backend/app/main.py`

```python
# backend/app/main.py
from fastapi import FastAPI
from .middleware.governance import GovernanceMiddleware

app = FastAPI()

# Governance 미들웨어 추가
app.add_middleware(GovernanceMiddleware)

# ... 나머지 라우터 등록
```

#### Day 4 오후: 승인 워크플로우

**파일 생성**: `backend/app/policy/approvals.py`

```python
# backend/app/policy/approvals.py
from datetime import datetime
from typing import Optional

def create_approval_if_needed(
    policy: dict,
    rule_id: str,
    requester_id: str,
    roles: list[str],
    payload: dict
) -> Optional[str]:
    """
    승인이 필요한지 확인하고, 필요하면 approval_request 생성
    
    Returns:
        approval_request_id if approval needed, None otherwise
    """
    approvals = policy.get('approvals', {})
    if not approvals.get('enabled'):
        return None
    
    # 해당 rule 찾기
    rule = None
    for r in approvals.get('rules', []):
        if r['id'] == rule_id:
            rule = r
            break
    
    if not rule:
        return None  # 규칙 없음 = 승인 불필요
    
    # Auto-approve 조건 확인
    auto_approve_conditions = rule.get('auto_approve_if', [])
    # TODO: 조건 평가 로직
    
    # 승인 요청 생성 (DB에 저장)
    # from ..models.governance import create_approval_request
    # approval_id = create_approval_request(...)
    
    return None  # or approval_id
```

---

### Day 5: 거버넌스 대시보드 MVP

#### Day 5: 간단한 Admin 페이지

**파일 생성**: `dashboards/governance-admin/index.html` (간단한 시작)

```html
<!DOCTYPE html>
<html>
<head>
    <title>Governance Dashboard</title>
    <style>
        body { font-family: Arial; padding: 20px; }
        .section { margin: 20px 0; padding: 15px; border: 1px solid #ccc; }
        button { padding: 10px 20px; margin: 5px; }
    </style>
</head>
<body>
    <h1>DreamSeedAI Governance Dashboard</h1>
    
    <div class="section">
        <h2>Current Policy Bundle</h2>
        <p>Bundle ID: <span id="bundle-id">Loading...</span></p>
        <p>Phase: <span id="phase">Loading...</span></p>
        <p>Mode: <span id="mode">Loading...</span></p>
        
        <button onclick="switchBundle('phase0')">Switch to Phase 0</button>
        <button onclick="switchBundle('phase1')">Switch to Phase 1</button>
        <button onclick="reloadPolicy()">Reload Policy</button>
    </div>
    
    <div class="section">
        <h2>Feature Flags</h2>
        <div id="feature-flags">Loading...</div>
    </div>
    
    <div class="section">
        <h2>Approval Queue</h2>
        <div id="approval-queue">Loading...</div>
    </div>
    
    <div class="section">
        <h2>Audit Log (Last 20)</h2>
        <div id="audit-log">Loading...</div>
    </div>
    
    <script>
        // TODO: API 호출로 실제 데이터 로드
        async function loadDashboard() {
            // fetch('/api/v1/governance/dashboard')
        }
        
        function switchBundle(bundleId) {
            // POST /api/v1/governance/switch-bundle
            alert(`Switching to ${bundleId}...`);
        }
        
        function reloadPolicy() {
            // POST /api/v1/governance/reload
            alert('Reloading policy...');
        }
        
        loadDashboard();
    </script>
</body>
</html>
```

**API 엔드포인트**: `backend/app/routers/governance.py`

```python
# backend/app/routers/governance.py
from fastapi import APIRouter, Depends
from ..policy.loader import load_policy_bundle, reload_policy
from ..settings import settings

router = APIRouter(prefix="/api/v1/governance", tags=["governance"])

@router.get("/dashboard")
async def get_dashboard():
    """거버넌스 대시보드 데이터"""
    policy = load_policy_bundle(settings.POLICY_BUNDLE_PATH)
    
    return {
        "bundle_id": policy['bundle_id'],
        "phase": policy['phase'],
        "mode": settings.POLICY_STRICT_MODE,
        "feature_flags": policy['feature_flags'],
        # TODO: approval_queue, audit_log
    }

@router.post("/reload")
async def reload_policy_endpoint():
    """정책 hot reload"""
    reload_policy()
    return {"status": "reloaded"}
```

---

### Day 6-7: 테스트 및 Phase 0 → 1 전환

#### Day 6 오전: 유닛 테스트

**파일 생성**: `backend/tests/test_governance_rbac.py`

```python
# backend/tests/test_governance_rbac.py
import pytest
from app.policy.rbac import check_permission

def test_rbac_admin_allow_all():
    policy = {
        'rbac': {
            'enabled': True,
            'roles': [
                {'name': 'admin', 'allows': ['*'], 'denies': []}
            ]
        }
    }
    
    assert check_permission(policy, ['admin'], 'any:action') == True

def test_rbac_deny_overrides_allow():
    policy = {
        'rbac': {
            'enabled': True,
            'roles': [
                {'name': 'user', 'allows': ['*'], 'denies': ['admin:write']}
            ]
        }
    }
    
    assert check_permission(policy, ['user'], 'admin:write') == False

def test_rbac_disabled():
    policy = {'rbac': {'enabled': False}}
    
    assert check_permission(policy, [], 'any:action') == True
```

**실행**:
```bash
pytest backend/tests/test_governance_rbac.py -v
```

#### Day 6 오후: E2E 테스트

```bash
# 1. Phase 0 (soft mode) 배포
export POLICY_BUNDLE_ID=phase0
export GOVERNANCE_PHASE=0
export POLICY_STRICT_MODE=soft

# 2. 실제 트래픽 모니터링
# - 감사 로그에서 policy_violation 이벤트 확인
# - 어떤 API가 차단될지 사전 파악

# 3. 경고 분석 후 Phase 1로 전환
export POLICY_BUNDLE_ID=phase1
export GOVERNANCE_PHASE=1
export POLICY_STRICT_MODE=enforce

# 4. 미들웨어가 실제로 차단하는지 확인
```

#### Day 7: 문서화 및 마무리

```bash
# 1. README 업데이트
# 2. 환경 변수 문서화
# 3. 팀 공유 및 데모
```

---

## 🎯 완료 체크리스트

### ✅ 완료된 것
- [x] `governance/` 디렉토리 구조 생성
- [x] 정책 번들 스키마 정의
- [x] Phase 1 정책 번들 작성
- [x] 검증 스크립트 (`validate.py`)
- [x] 컴파일 스크립트 (`compile.py`)
- [x] 문서 이동 및 정리

### ⏳ 다음 단계 (1주 계획)
- [ ] Phase 0, 2 정책 번들 작성
- [ ] 데이터베이스 마이그레이션 실행
- [ ] Settings 및 Policy Loader 구현
- [ ] RBAC, Feature Flags, Content Filter 구현
- [ ] Governance Middleware 구현 및 통합
- [ ] 승인 워크플로우 구현
- [ ] 거버넌스 대시보드 MVP
- [ ] 테스트 및 검증
- [ ] Phase 0 → 1 전환

---

## 🔧 사용법

### 정책 번들 검증
```bash
python governance/scripts/validate.py governance/bundles/policy_bundle_phase1.yaml
```

### 정책 번들 컴파일
```bash
python governance/scripts/compile.py governance/bundles/policy_bundle_phase1.yaml
```

### 환경 변수 설정
```bash
export POLICY_BUNDLE_ID=phase1
export GOVERNANCE_PHASE=1
export POLICY_STRICT_MODE=soft
export POLICY_BUNDLE_PATH=governance/compiled/phase1.json
```

### FastAPI 실행
```bash
cd backend
uvicorn app.main:app --reload
```

---

## 📚 참고 자료

- [거버넌스 철학](../governance/docs/GOVERNANCE_PHILOSOPHY.md)
- [거버넌스 운영](../governance/docs/GOVERNANCE_LAYER_OPERATIONS.md)
- [Policy Bundle Schema](../governance/schemas/policy-bundle.schema.json)

---

**Last Updated**: 2025-11-07  
**Status**: Ready for Implementation  
**Owner**: DreamSeedAI Backend Team
