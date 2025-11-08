# DreamSeedAI Governance - Route to Action Mapping

**버전**: v1.0 (2025-01-20)  
**목적**: DreamSeedAI MVP API 엔드포인트 → Governance Action Key 매핑  
**구현 위치**: `backend/app/middleware/policy_routes.py`

---

## 📋 서비스별 Route → Action 매핑표

### 1. Classes (클래스/학급)

| Method | Path Pattern | Action Key | Feature Flag | Approval Rule | Notes |
|--------|-------------|-----------|--------------|---------------|-------|
| GET | `/api/v1/classes/{id}/snapshot` | `class:read` | - | - | 클래스 스냅샷 조회 |
| GET | `/api/v1/classes/{id}/students` | `class:read` | - | - | 클래스 학생 목록 |
| GET | `/api/v1/classes/{id}/risk/summary` | `risk:read` | `risk_engine` | - | 위험도 요약 (위험 엔진 필요) |
| POST | `/api/v1/classes` | `class:write` | - | - | 클래스 생성 |
| PUT | `/api/v1/classes/{id}` | `class:update` | - | - | 클래스 수정 |
| PATCH | `/api/v1/classes/{id}` | `class:update` | - | - | 클래스 부분 수정 |
| DELETE | `/api/v1/classes/{id}` | `class:delete` | - | - | 클래스 삭제 |

### 2. Students (학생)

| Method | Path Pattern | Action Key | Feature Flag | Approval Rule | Notes |
|--------|-------------|-----------|--------------|---------------|-------|
| GET | `/api/v1/students/{id}/timeline` | `student:read` | - | - | 학생 타임라인 |
| GET | `/api/v1/students/{id}` | `student:read` | - | - | 학생 상세 조회 |
| POST | `/api/v1/students` | `student:write` | - | - | 학생 등록 |
| PUT | `/api/v1/students/{id}` | `student:update` | - | - | 학생 정보 수정 |
| PATCH | `/api/v1/students/{id}` | `student:update` | - | - | 학생 정보 부분 수정 |
| DELETE | `/api/v1/students/{id}` | `student:delete` | - | - | 학생 삭제 |

### 3. Assignments (과제)

| Method | Path Pattern | Action Key | Feature Flag | Approval Rule | Notes |
|--------|-------------|-----------|--------------|---------------|-------|
| POST | `/api/v1/assignments` | `assignment:create` | - | `content.newitem` | 과제 생성 (48h 승인) |
| GET | `/api/v1/assignments/{id}` | `assignment:read` | - | - | 과제 조회 |
| PUT | `/api/v1/assignments/{id}` | `assignment:update` | - | - | 과제 수정 |
| PATCH | `/api/v1/assignments/{id}` | `assignment:update` | - | - | 과제 부분 수정 |
| DELETE | `/api/v1/assignments/{id}` | `assignment:delete` | - | - | 과제 삭제 |

### 4. Assignment Templates (과제 템플릿)

| Method | Path Pattern | Action Key | Feature Flag | Approval Rule | Notes |
|--------|-------------|-----------|--------------|---------------|-------|
| GET | `/api/v1/assignment-templates` | `assignment:template:read` | - | - | 템플릿 목록 |
| GET | `/api/v1/assignment-templates/{id}` | `assignment:template:read` | - | - | 템플릿 상세 |

### 5. Tutor (AI 튜터)

| Method | Path Pattern | Action Key | Feature Flag | Approval Rule | Notes |
|--------|-------------|-----------|--------------|---------------|-------|
| POST | `/api/v1/tutor/query` | `tutor:ask` | - | - | AI 튜터 질문 (시험 시 차단) |
| GET | `/api/v1/tutor/sessions/{id}` | `tutor:read` | - | - | 튜터 세션 조회 |
| GET | `/api/v1/tutor/sessions` | `tutor:read` | - | - | 튜터 세션 목록 |

### 6. Risk Engine (위험도 분석)

| Method | Path Pattern | Action Key | Feature Flag | Approval Rule | Notes |
|--------|-------------|-----------|--------------|---------------|-------|
| GET | `/api/v1/risk/students/{id}` | `risk:read` | `risk_engine` | - | 학생 위험도 조회 |
| POST | `/api/v1/risk/analyze` | `risk:write` | `risk_engine` | - | 위험도 분석 실행 |

### 7. Content (콘텐츠 제안/승인)

| Method | Path Pattern | Action Key | Feature Flag | Approval Rule | Notes |
|--------|-------------|-----------|--------------|---------------|-------|
| POST | `/api/v1/content/propose` | `content:propose` | - | `ai_content_recommendation` | AI 콘텐츠 제안 (48h 승인) |
| POST | `/api/v1/content/approve` | `content:approve` | - | - | 콘텐츠 승인 (teacher만) |

### 8. Exams (시험)

| Method | Path Pattern | Action Key | Feature Flag | Approval Rule | Notes |
|--------|-------------|-----------|--------------|---------------|-------|
| GET | `/api/v1/exams/{id}` | `exam:read` | `exam_pipeline` | - | 시험 조회 |
| POST | `/api/v1/exams` | `exam:create` | `exam_pipeline` | - | 시험 생성 |

### 9. Parent Portal (학부모 포털)

| Method | Path Pattern | Action Key | Feature Flag | Approval Rule | Notes |
|--------|-------------|-----------|--------------|---------------|-------|
| GET | `/api/v1/parent/children` | `own_children:read` | `parent_portal` | - | 자녀 목록 조회 |
| GET | `/api/v1/parent/children/{id}` | `own_children:read` | `parent_portal` | - | 자녀 상세 조회 |
| POST | `/api/v1/parent/consent` | `consent:manage` | `parent_portal` | - | 동의 관리 |
| POST | `/api/v1/parent/data-deletion` | `data_deletion:request` | `parent_portal` | `data_deletion_request` | 데이터 삭제 요청 (7일 승인) |

### 10. Internal (내부 관리 API)

| Method | Path Pattern | Action Key | Feature Flag | Approval Rule | Notes |
|--------|-------------|-----------|--------------|---------------|-------|
| POST | `/internal/policy/reload` | `policy:write` | - | - | 정책 번들 핫 리로드 (Admin만) |
| GET | `/internal/policy/status` | `policy:read` | - | - | 정책 상태 조회 |
| GET | `/internal/audit/logs` | `audit:read` | - | - | 감사 로그 조회 (Admin만) |

### 11. Health Checks (헬스체크)

| Method | Path Pattern | Action Key | Feature Flag | Approval Rule | Notes |
|--------|-------------|-----------|--------------|---------------|-------|
| GET | `/healthz` | `meta:read` | - | - | Public 헬스체크 |
| GET | `/readyz` | `meta:read` | - | - | Readiness 체크 |
| GET | `/__ok` | `meta:read` | - | - | 레거시 헬스체크 |

---

## 🔐 RBAC 권한 매트릭스

### Role: `admin` (플랫폼 관리자)
- **Allows**: `["*"]` (모든 액션)
- **Key Actions**: 정책 관리, 감사 로그, 모든 데이터 접근

### Role: `teacher` (교사)
- **Allows**: 
  - `class:*` (클래스 전체 관리)
  - `student:read`, `student:update` (학생 조회/수정)
  - `assignment:*` (과제 전체 관리)
  - `tutor:read` (튜터 세션 조회)
  - `content:approve` (콘텐츠 승인)
- **Denies**: 학생 삭제, 정책 변경

### Role: `counselor` (상담사)
- **Allows**:
  - `class:read`
  - `student:read`
  - `risk:read` (위험도 조회)
  - `tutor:read`
- **Denies**: 쓰기 작업

### Role: `parent` (학부모)
- **Allows**:
  - `own_children:read` (자녀만 조회)
  - `consent:manage` (동의 관리)
  - `data_deletion:request` (데이터 삭제 요청)
- **Denies**: 다른 학생 데이터 접근

### Role: `student` (학생)
- **Allows**:
  - `self:read` (본인 데이터 조회)
  - `tutor:ask` (튜터 질문)
  - `assignment:submit` (과제 제출)
- **Denies**: 다른 학생 데이터, 클래스 관리

### Role: `viewer` (읽기 전용)
- **Allows**:
  - `class:read`
  - `student:read`
  - `assignment:read`
- **Denies**: 모든 쓰기 작업

---

## 🚩 Feature Flags

### `risk_engine` (위험도 엔진)
- **Required for**: `risk:read`, `risk:write`
- **Phase**: Phase 2+
- **Endpoints**:
  - `GET /api/v1/classes/{id}/risk/summary`
  - `GET /api/v1/risk/students/{id}`
  - `POST /api/v1/risk/analyze`

### `exam_pipeline` (시험 파이프라인)
- **Required for**: `exam:*`
- **Phase**: Phase 2+
- **Endpoints**:
  - `GET /api/v1/exams/{id}`
  - `POST /api/v1/exams`

### `parent_portal` (학부모 포털)
- **Required for**: `own_children:*`, `consent:*`, `data_deletion:*`
- **Phase**: Phase 2+
- **Endpoints**:
  - `GET /api/v1/parent/children`
  - `POST /api/v1/parent/consent`
  - `POST /api/v1/parent/data-deletion`

### `fairness_monitoring` (공정성 모니터링)
- **Required for**: AI 콘텐츠 제안 시 바이어스 체크
- **Phase**: Phase 3
- **Endpoints**: `/api/v1/content/propose`

---

## ✅ Approval Rules

### `content.newitem` (과제/콘텐츠 생성)
- **Triggered by**: `POST /api/v1/assignments`
- **Approver Role**: `teacher`
- **SLA**: 48 hours
- **Auto-approve**: 없음

### `ai_content_recommendation` (AI 콘텐츠 제안)
- **Triggered by**: `POST /api/v1/content/propose`
- **Approver Role**: `teacher`
- **SLA**: 48 hours
- **Auto-approve**: `risk_score < 0.3`

### `data_deletion_request` (데이터 삭제 요청)
- **Triggered by**: `POST /api/v1/parent/data-deletion`
- **Approver Role**: `admin`
- **SLA**: 168 hours (7일)
- **Auto-approve**: 없음

---

## 📦 구현 파일

### 1. Route Mapping Logic
**File**: `backend/app/middleware/policy_routes.py`

```python
from typing import Optional, Tuple
import re

def route_to_action(method: str, path: str) -> Tuple[str, Optional[str], Optional[str]]:
    """
    Returns: (action, required_flag, approval_rule)
    """
    # Regex 기반 패턴 매칭
    # 예: ("GET", r"^/api/v1/classes/\d+/snapshot$", "class:read", None, None)
```

### 2. Middleware Integration
**File**: `backend/app/middleware/policy.py`

```python
from app.middleware.policy_routes import route_to_action as route_map

class GovernanceMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        action, required_flag, approval_rule = route_map(
            request.method, 
            request.url.path
        )
        
        # RBAC 체크
        has_permission = check_permission(POLICY, roles, action)
        
        # Feature Flag 체크
        if required_flag and not feature_enabled(POLICY, required_flag):
            return Response(status_code=403)
```

### 3. Policy Bundle
**File**: `governance/bundles/policy_bundle_phase1.yaml`

```yaml
rbac:
  roles:
    teacher:
      allows:
        - "class:*"
        - "assignment:*"
        - "student:read"
      denies:
        - "student:delete"
```

---

## 🧪 테스트 커맨드

### Preflight Check (컴파일 + 파일 검증)
```bash
bash ops/scripts/governance_preflight_check.sh
```

### Runtime Tests (cURL 기반)
```bash
bash ops/scripts/governance_runtime_test.sh https://staging.dreamseed.ai
```

### Manual API Test
```bash
# RBAC 체크 (viewer는 POST 차단)
curl -X POST https://api.dreamseed.ai/api/v1/assignments \
  -H "X-Roles: viewer" \
  -H "Content-Type: application/json" \
  -d '{"title":"Test"}' \
  # Expected: 403 Forbidden

# Feature Flag 체크 (risk_engine=false 시 차단)
curl -X GET https://api.dreamseed.ai/api/v1/risk/students/123 \
  -H "X-Roles: teacher" \
  # Expected: 403 if risk_engine disabled

# Policy Status
curl https://api.dreamseed.ai/internal/policy/status | jq
```

---

## 📝 변경 이력

### v1.0 (2025-01-20)
- DreamSeedAI MVP API 기준 초기 매핑 완료
- 11개 서비스, 40+ 엔드포인트 커버
- Regex 기반 route_to_action 구현 (`policy_routes.py`)
- Feature Flag 연동 (risk_engine, exam_pipeline, parent_portal)
- Approval Rule 연동 (content.newitem, ai_content_recommendation, data_deletion_request)

---

## 🔗 관련 문서

- **Policy Bundle Schema**: `governance/schemas/policy-bundle.schema.json`
- **Deployment Guide**: `GOVERNANCE_DEPLOYMENT_CHECKLIST.md`
- **Quick Start**: `GOVERNANCE_QUICKSTART.md`
- **Commit Guide**: `GOVERNANCE_COMMIT_GUIDE.md`
