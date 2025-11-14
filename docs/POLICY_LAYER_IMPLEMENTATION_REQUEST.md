# DreamSeedAI 정책 계층 (Policy Layer) 구현 요청서

**프로젝트**: DreamSeedAI Monorepo  
**브랜치**: feat/governance-production-ready  
**요청일**: 2025-11-08  
**우선순위**: High  
**예상 기간**: 4-6주

---

## 📋 요청 개요

DreamSeedAI의 거버넌스 시스템 중 **정책 계층 (Policy Layer)** 을 구현해 주세요. 정책 계층은 거버넌스 계층의 원칙을 실제 시스템 규칙으로 구현하고, AI 행동을 제어하며, 사용자 권한을 관리하는 핵심 계층입니다.

**참고 문서**: `/home/won/projects/dreamseed_monorepo/docs/POLICY_LAYER_DESIGN.md` (3,500+ 라인)

---

## 🎯 구현 목표

### 핵심 요구사항

1. **중앙 정책 엔진**: Open Policy Agent (OPA) 기반 정책 평가 시스템 구축
2. **분산 정책 훅**: FastAPI 마이크로서비스에 정책 검사 데코레이터/미들웨어 적용
3. **실시간 정책 업데이트**: ConfigMap 기반 Hot-Reload 구현
4. **다층 방어**: 접근 제어, AI 콘텐츠 정책, 승인 워크플로우 통합
5. **모니터링 및 감사**: Prometheus/Grafana 통합 및 Slack 알림

### 성공 기준

- [ ] OPA 정책 엔진이 Kubernetes 클러스터에 배포되어 정상 작동
- [ ] 최소 6개 정책 예시 (접근 제어, AI 콘텐츠, 승인 등) 구현
- [ ] FastAPI 백엔드에서 정책 평가 데코레이터 사용 가능
- [ ] ConfigMap 변경 시 무중단 Hot-Reload 동작
- [ ] Prometheus 메트릭 수집 및 Grafana 대시보드 표시
- [ ] 정책 위반 시 Slack 알림 전송
- [ ] 단위 테스트 및 통합 테스트 통과 (커버리지 80% 이상)

---

## 🏗️ 구현 범위

### Phase 1: 핵심 정책 엔진 (2주)

#### 1.1 OPA 배포 및 설정

**위치**: `ops/k8s/governance/`

**구현 내용**:

```yaml
# ops/k8s/governance/base/deployment-opa.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: opa-policy-engine
  namespace: governance
spec:
  replicas: 2
  selector:
    matchLabels:
      app: opa
  template:
    metadata:
      labels:
        app: opa
    spec:
      containers:
      - name: opa
        image: openpolicyagent/opa:0.58.0-rootless
        args:
          - "run"
          - "--server"
          - "--addr=0.0.0.0:8181"
          - "--config-file=/config/opa-config.yaml"
          - "/policies"
        ports:
          - containerPort: 8181
            name: http
        volumeMounts:
          - name: opa-config
            mountPath: /config
          - name: policy-bundle
            mountPath: /policies
        livenessProbe:
          httpGet:
            path: /health
            port: 8181
          initialDelaySeconds: 10
        readinessProbe:
          httpGet:
            path: /health?bundle=true
            port: 8181
          initialDelaySeconds: 5
      volumes:
        - name: opa-config
          configMap:
            name: opa-config
        - name: policy-bundle
          configMap:
            name: governance-policy-bundle
```

**요청 사항**:
- OPA Deployment, Service, ServiceMonitor 매니페스트 작성
- ConfigMap 기반 정책 번들 마운트
- Health check 및 Readiness probe 설정
- HPA (Horizontal Pod Autoscaler) 설정 (CPU 70% 기준)

#### 1.2 Rego 정책 작성

**위치**: `governance/bundles/`

**구현할 정책** (최소 6개):

1. **접근 제어 정책** (`access_control.rego`):
   - 역할 기반 접근 제어 (RBAC)
   - 사용자 역할: student, teacher, parent, admin
   - 리소스별 권한 매핑

```rego
# 예시
package dreamseedai.access_control

default allow = false

allow {
    input.user.role == "admin"
}

allow {
    input.user.role == "teacher"
    input.resource.type == "lesson"
    input.action == "read"
}

allow {
    input.user.role == "student"
    input.resource.type == "lesson"
    input.action == "read"
    is_grade_appropriate(input.user, input.resource)
}

is_grade_appropriate(user, resource) {
    user.grade >= resource.min_grade
    user.grade <= resource.max_grade
}
```

2. **AI 콘텐츠 정책** (`ai_content_policy.rego`):
   - 금지어 필터링
   - 민감 주제 탐지 (정치, 종교, 성, 폭력)
   - 학년별 적합성 검사

3. **AI 행동 정책** (`ai_behavior_policy.rego`):
   - AI 응답 길이 제한
   - 외부 링크 차단
   - 과제 대신 작성 방지

4. **승인 워크플로우 정책** (`approval_policy.rego`):
   - 고위험 액션 식별
   - 승인자 권한 검증
   - 타임아웃 설정

5. **데이터 보호 정책** (`data_protection.rego`):
   - 개인정보 접근 제어
   - 학부모 동의 검증
   - 데이터 보존 기간 확인

6. **사용량 제한 정책** (`rate_limit.rego`):
   - 사용자별 API 호출 제한
   - AI 튜터 세션 시간 제한
   - 리소스 쿼터 관리

**요청 사항**:
- 각 정책을 별도 `.rego` 파일로 작성
- 정책별 단위 테스트 (`*_test.rego`) 작성
- 정책 컴파일 스크립트 (`governance/scripts/compile.py`) 업데이트

#### 1.3 ConfigMap 및 Hot-Reload

**위치**: `ops/k8s/governance/base/`

**구현 내용**:

```yaml
# configmap-policy-bundle.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: governance-policy-bundle
  namespace: governance
  annotations:
    policy.version: "1.0.0"
    policy.environment: "production"
data:
  policy.json: |
    {
      "bundles": {
        "access_control": { ... },
        "ai_content": { ... },
        "ai_behavior": { ... },
        "approval": { ... },
        "data_protection": { ... },
        "rate_limit": { ... }
      }
    }
```

**요청 사항**:
- ConfigMap Hash를 Deployment annotation으로 주입하여 자동 재시작
- OPA 측에서 ConfigMap 변경 감지 및 재로드 구현
- 롤백 메커니즘 (이전 ConfigMap 버전 유지)

---

### Phase 2: FastAPI 백엔드 통합 (1.5주)

#### 2.1 정책 평가 클라이언트

**위치**: `governance/backend/policy_client.py`

**구현 내용**:

```python
# governance/backend/policy_client.py
import httpx
from typing import Dict, Any, Optional
from functools import lru_cache

class PolicyEngineClient:
    """OPA 정책 엔진 클라이언트"""
    
    def __init__(self, opa_url: str = "http://opa-policy-engine.governance.svc.cluster.local:8181"):
        self.opa_url = opa_url
        self.client = httpx.AsyncClient(timeout=2.0)
    
    async def evaluate(
        self,
        policy_path: str,
        input_data: Dict[str, Any],
        return_full_result: bool = False
    ) -> Dict[str, Any]:
        """
        정책 평가 요청
        
        Args:
            policy_path: 정책 경로 (예: "dreamseedai/access_control/allow")
            input_data: 평가할 입력 데이터
            return_full_result: 전체 결과 반환 여부
        
        Returns:
            정책 평가 결과
        """
        url = f"{self.opa_url}/v1/data/{policy_path.replace('.', '/')}"
        
        try:
            response = await self.client.post(url, json={"input": input_data})
            response.raise_for_status()
            result = response.json()
            
            if return_full_result:
                return result
            
            # 기본적으로 result.allow 값만 반환
            return result.get("result", {})
        
        except httpx.HTTPError as e:
            # 정책 평가 실패 시 기본 deny
            return {"allow": False, "error": str(e)}
    
    async def close(self):
        await self.client.aclose()

@lru_cache
def get_policy_client() -> PolicyEngineClient:
    """정책 클라이언트 싱글톤 인스턴스 반환"""
    return PolicyEngineClient()
```

**요청 사항**:
- OPA HTTP API 호출 클라이언트 구현
- 비동기 (async/await) 지원
- 타임아웃 및 재시도 로직
- 캐싱 전략 (선택 사항)
- 에러 핸들링 (정책 평가 실패 시 기본 deny)

#### 2.2 FastAPI 데코레이터

**위치**: `governance/backend/decorators.py`

**구현 내용**:

```python
# governance/backend/decorators.py
from fastapi import Depends, HTTPException, Request
from functools import wraps
from typing import Callable, Optional, Dict, Any
from .policy_client import get_policy_client, PolicyEngineClient

def require_policy(
    policy_path: str,
    input_builder: Optional[Callable] = None,
    deny_status_code: int = 403
):
    """
    정책 평가 데코레이터
    
    Args:
        policy_path: 평가할 정책 경로 (예: "dreamseedai.access_control.allow")
        input_builder: 정책 입력 데이터 생성 함수
        deny_status_code: 거부 시 HTTP 상태 코드
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Request 객체 추출
            request: Optional[Request] = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            if not request:
                request = kwargs.get("request")
            
            # 정책 입력 데이터 생성
            if input_builder:
                input_data = await input_builder(request, *args, **kwargs)
            else:
                # 기본 입력 데이터 (사용자 정보, 요청 정보)
                input_data = {
                    "user": getattr(request.state, "user", {}),
                    "resource": {
                        "path": request.url.path,
                        "method": request.method
                    },
                    "action": request.method.lower()
                }
            
            # 정책 평가
            policy_client = get_policy_client()
            result = await policy_client.evaluate(policy_path, input_data)
            
            # 정책 거부 시 예외 발생
            if not result.get("allow", False):
                raise HTTPException(
                    status_code=deny_status_code,
                    detail={
                        "error": "Policy violation",
                        "policy": policy_path,
                        "reason": result.get("reason", "Access denied")
                    }
                )
            
            # 정책 통과 시 원래 함수 실행
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator
```

**사용 예시**:

```python
# backend/api/lessons.py
from fastapi import APIRouter, Depends
from governance.backend.decorators import require_policy

router = APIRouter()

@router.get("/lessons/{lesson_id}")
@require_policy("dreamseedai.access_control.allow")
async def get_lesson(lesson_id: int, request: Request):
    """레슨 조회 (정책 검사 적용)"""
    # 정책 통과 시에만 실행됨
    return {"lesson_id": lesson_id, "content": "..."}
```

**요청 사항**:
- FastAPI 라우트 함수에 적용 가능한 데코레이터 구현
- 정책 평가 결과에 따라 403 Forbidden 또는 200 OK 반환
- 사용자 정의 입력 데이터 빌더 지원
- Prometheus 메트릭 수집 (정책 평가 횟수, 거부 횟수, 지연시간)

#### 2.3 미들웨어 (전역 정책 적용)

**위치**: `governance/backend/middleware.py`

**구현 내용**:

```python
# governance/backend/middleware.py
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from .policy_client import get_policy_client

class PolicyEnforcementMiddleware(BaseHTTPMiddleware):
    """전역 정책 검사 미들웨어"""
    
    async def dispatch(self, request: Request, call_next):
        # 정책 평가가 필요한 엔드포인트인지 확인
        if self._should_evaluate(request):
            # 정책 평가
            policy_client = get_policy_client()
            result = await policy_client.evaluate(
                "dreamseedai.access_control.allow",
                {
                    "user": getattr(request.state, "user", {}),
                    "resource": {
                        "path": request.url.path,
                        "method": request.method
                    }
                }
            )
            
            # 정책 거부 시 403 반환
            if not result.get("allow", False):
                return JSONResponse(
                    status_code=403,
                    content={"error": "Access denied by policy"}
                )
        
        # 다음 미들웨어/라우트 핸들러 실행
        response = await call_next(request)
        return response
    
    def _should_evaluate(self, request: Request) -> bool:
        """정책 평가 필요 여부 판단"""
        # health check, metrics 엔드포인트는 제외
        excluded_paths = ["/health", "/metrics", "/docs", "/openapi.json"]
        return request.url.path not in excluded_paths
```

**요청 사항**:
- Starlette 미들웨어 구현
- 특정 경로 제외 기능 (health check, metrics 등)
- 비동기 정책 평가
- 메트릭 수집

---

### Phase 3: 모니터링 및 감사 (1주)

#### 3.1 Prometheus 메트릭

**위치**: `governance/backend/metrics.py`

**구현할 메트릭** (19개):

```python
# governance/backend/metrics.py
from prometheus_client import Counter, Histogram, Gauge

# 정책 평가 메트릭
policy_evaluations_total = Counter(
    "governance_policy_evaluations_total",
    "Total number of policy evaluations",
    ["policy", "result"]
)

policy_deny_total = Counter(
    "governance_policy_deny_total",
    "Total number of policy denials",
    ["policy", "user_role"]
)

policy_evaluation_duration = Histogram(
    "governance_policy_evaluation_duration_seconds",
    "Policy evaluation duration in seconds",
    ["policy"]
)

# 정책 번들 메트릭
policy_bundle_reload_total = Counter(
    "governance_policy_bundle_reload_total",
    "Total number of policy bundle reloads",
    ["status"]
)

policy_bundle_version = Gauge(
    "governance_policy_bundle_version",
    "Current policy bundle version"
)

# AI 콘텐츠 메트릭
ai_content_filtered_total = Counter(
    "governance_ai_content_filtered_total",
    "Total number of AI content filtered",
    ["filter_type", "severity"]
)

ai_tutor_sessions_total = Counter(
    "governance_ai_tutor_sessions_total",
    "Total number of AI tutor sessions",
    ["user_role", "status"]
)

# 승인 워크플로우 메트릭
approval_requests_total = Counter(
    "governance_approval_requests_total",
    "Total number of approval requests",
    ["action_type", "status"]
)

approval_pending_gauge = Gauge(
    "governance_approval_pending",
    "Number of pending approvals"
)

# 데이터 보호 메트릭
data_access_total = Counter(
    "governance_data_access_total",
    "Total number of data access attempts",
    ["data_type", "result"]
)
```

**요청 사항**:
- 19개 메트릭 정의 및 구현
- 데코레이터/미들웨어에서 메트릭 자동 수집
- `/metrics` 엔드포인트 노출 (FastAPI)

#### 3.2 Grafana 대시보드

**위치**: `infra/monitoring/grafana/dashboards/governance-policy-dashboard.json`

**구현 내용**:

- **Panel 1**: 정책 평가 성공/실패율 (Pie Chart)
- **Panel 2**: 정책별 평가 횟수 (Bar Chart)
- **Panel 3**: 정책 평가 지연시간 (Heatmap)
- **Panel 4**: 정책 거부 사유 Top 10 (Table)
- **Panel 5**: AI 콘텐츠 필터링 추이 (Time Series)
- **Panel 6**: 승인 대기 건수 (Gauge)
- **Panel 7**: 사용자별 정책 위반 Top 10 (Table)
- **Panel 8**: 정책 번들 버전 (Stat)

**요청 사항**:
- Grafana 대시보드 JSON 파일 생성
- 16개 패널 구성 (시각화 유형 다양화)
- 변수 (Variable) 설정 (환경, 정책 이름 등)
- 알림 규칙 (Alert Rule) 통합

#### 3.3 Alertmanager 알림

**위치**: `infra/monitoring/prometheus/rules/governance-alerts.yaml`

**구현할 알림 규칙** (15개):

```yaml
# governance-alerts.yaml
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: governance-alerts
  namespace: monitoring
spec:
  groups:
    - name: policy_violations
      interval: 30s
      rules:
        # 1. 정책 거부율 급증
        - alert: HighPolicyDenyRate
          expr: |
            rate(governance_policy_deny_total[5m]) > 10
          for: 2m
          labels:
            severity: warning
            service: governance
          annotations:
            summary: "High policy denial rate detected"
            description: "Policy {{ $labels.policy }} denial rate is {{ $value }} denials/sec"
        
        # 2. 정책 평가 실패
        - alert: PolicyEvaluationFailure
          expr: |
            rate(governance_policy_errors_total[5m]) > 1
          for: 1m
          labels:
            severity: critical
            service: governance
          annotations:
            summary: "Policy evaluation failures detected"
            description: "Policy {{ $labels.policy }} evaluation error rate is {{ $value }}/sec"
        
        # 3. AI 콘텐츠 필터링 급증
        - alert: AIContentFilteringSpike
          expr: |
            rate(governance_ai_content_filtered_total{severity="high"}[5m]) > 5
          for: 2m
          labels:
            severity: warning
            service: governance
          annotations:
            summary: "High AI content filtering rate"
            description: "AI content filtered {{ $value }} times/sec (filter: {{ $labels.filter_type }})"
        
        # 4. 승인 대기 건수 과다
        - alert: ApprovalBacklog
          expr: |
            governance_approval_pending > 50
          for: 5m
          labels:
            severity: warning
            service: governance
          annotations:
            summary: "Approval backlog detected"
            description: "{{ $value }} approvals are pending"
        
        # 5. 정책 번들 리로드 실패
        - alert: PolicyBundleReloadFailure
          expr: |
            rate(governance_policy_bundle_reload_total{status="error"}[5m]) > 0
          for: 1m
          labels:
            severity: critical
            service: governance
          annotations:
            summary: "Policy bundle reload failed"
            description: "Policy bundle reload failures detected"
```

**요청 사항**:
- 15개 알림 규칙 정의
- 심각도 (severity) 구분: critical, warning, info
- Slack 라우팅 설정 (Critical → #seedtest-alerts, Warning → #seedtest-alerts)
- 알림 메시지 템플릿 (summary, description)

---

### Phase 4: 테스트 및 문서화 (1주)

#### 4.1 단위 테스트

**위치**: `governance/tests/`

**구현 내용**:

```python
# governance/tests/test_policy_client.py
import pytest
from governance.backend.policy_client import PolicyEngineClient

@pytest.mark.asyncio
async def test_access_control_allow():
    """관리자 접근 허용 테스트"""
    client = PolicyEngineClient()
    
    result = await client.evaluate(
        "dreamseedai.access_control.allow",
        {
            "user": {"role": "admin"},
            "resource": {"type": "lesson"},
            "action": "delete"
        }
    )
    
    assert result["allow"] == True

@pytest.mark.asyncio
async def test_access_control_deny():
    """학생 삭제 거부 테스트"""
    client = PolicyEngineClient()
    
    result = await client.evaluate(
        "dreamseedai.access_control.allow",
        {
            "user": {"role": "student"},
            "resource": {"type": "lesson"},
            "action": "delete"
        }
    )
    
    assert result["allow"] == False
```

**요청 사항**:
- 정책 클라이언트 단위 테스트 (10개 이상)
- 데코레이터 단위 테스트 (5개 이상)
- 미들웨어 통합 테스트 (3개 이상)
- Rego 정책 테스트 (`*_test.rego`, 각 정책당 5개 이상)
- pytest-asyncio 사용
- 커버리지 80% 이상

#### 4.2 통합 테스트

**위치**: `governance/tests/integration/`

**구현 내용**:

```python
# governance/tests/integration/test_policy_enforcement.py
import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_student_cannot_delete_lesson():
    """학생은 레슨 삭제 불가 (통합 테스트)"""
    response = client.delete(
        "/lessons/123",
        headers={"Authorization": "Bearer STUDENT_TOKEN"}
    )
    
    assert response.status_code == 403
    assert "Access denied" in response.json()["detail"]

def test_teacher_can_delete_lesson():
    """교사는 레슨 삭제 가능 (통합 테스트)"""
    response = client.delete(
        "/lessons/123",
        headers={"Authorization": "Bearer TEACHER_TOKEN"}
    )
    
    assert response.status_code == 200
```

**요청 사항**:
- FastAPI 엔드포인트 통합 테스트 (10개 이상)
- Kubernetes 환경 통합 테스트 (선택 사항)
- 시나리오 기반 테스트 (예: 학생 → AI 튜터 → 필터링 → 승인)

#### 4.3 문서화

**위치**: `ops/k8s/governance/`

**작성할 문서**:

1. **DEPLOYMENT_GUIDE.md**:
   - OPA 배포 절차
   - ConfigMap 업데이트 방법
   - 롤백 절차
   - 트러블슈팅

2. **POLICY_DEVELOPMENT_GUIDE.md**:
   - Rego 정책 작성 가이드
   - 정책 테스트 방법
   - 정책 컴파일 및 배포
   - 베스트 프랙티스

3. **API_REFERENCE.md**:
   - PolicyEngineClient API 문서
   - 데코레이터 사용법
   - 입력 데이터 스키마
   - 예제 코드

4. **MONITORING_GUIDE.md**:
   - Grafana 대시보드 사용법
   - 알림 규칙 설정
   - 메트릭 해석
   - 성능 튜닝

**요청 사항**:
- 각 문서 1,000+ 라인 이상
- 코드 예시 포함
- 다이어그램/플로우차트 (선택 사항)
- 운영 체크리스트

---

## 📂 디렉토리 구조

```
dreamseed_monorepo/
├── governance/
│   ├── bundles/
│   │   ├── access_control.rego
│   │   ├── ai_content_policy.rego
│   │   ├── ai_behavior_policy.rego
│   │   ├── approval_policy.rego
│   │   ├── data_protection.rego
│   │   └── rate_limit.rego
│   ├── backend/
│   │   ├── __init__.py
│   │   ├── policy_client.py
│   │   ├── decorators.py
│   │   ├── middleware.py
│   │   └── metrics.py
│   ├── tests/
│   │   ├── test_policy_client.py
│   │   ├── test_decorators.py
│   │   ├── test_middleware.py
│   │   └── integration/
│   │       └── test_policy_enforcement.py
│   └── scripts/
│       ├── compile.py
│       └── validate.py
├── ops/k8s/governance/
│   ├── base/
│   │   ├── deployment-opa.yaml
│   │   ├── service-opa.yaml
│   │   ├── servicemonitor-opa.yaml
│   │   ├── configmap-opa-config.yaml
│   │   ├── configmap-policy-bundle.yaml
│   │   └── hpa-opa.yaml
│   ├── overlays/
│   │   ├── dev/
│   │   ├── staging/
│   │   └── production/
│   ├── DEPLOYMENT_GUIDE.md
│   ├── POLICY_DEVELOPMENT_GUIDE.md
│   └── MONITORING_GUIDE.md
├── infra/monitoring/
│   ├── prometheus/
│   │   └── rules/
│   │       └── governance-alerts.yaml
│   └── grafana/
│       └── dashboards/
│           └── governance-policy-dashboard.json
└── docs/
    ├── POLICY_LAYER_DESIGN.md (이미 작성됨)
    └── POLICY_LAYER_IMPLEMENTATION_REQUEST.md (이 문서)
```

---

## 🔧 기술 스택

| 컴포넌트 | 기술 | 버전 |
|---------|------|------|
| 정책 엔진 | Open Policy Agent (OPA) | 0.58.0+ |
| 정책 언어 | Rego | - |
| 백엔드 | FastAPI | 0.104.0+ |
| HTTP 클라이언트 | httpx | 0.25.0+ |
| 오케스트레이션 | Kubernetes | 1.28+ |
| 모니터링 | Prometheus + Grafana | - |
| 알림 | Alertmanager → Slack | - |
| 테스트 | pytest, pytest-asyncio | - |

---

## 📊 성능 요구사항

| 메트릭 | 목표 |
|--------|------|
| 정책 평가 지연시간 (P95) | < 50ms |
| 정책 평가 지연시간 (P99) | < 100ms |
| OPA 가용성 | > 99.9% |
| ConfigMap Hot-Reload 시간 | < 30초 |
| 메모리 사용량 (OPA Pod) | < 256MB |
| CPU 사용량 (OPA Pod) | < 500m |
| 정책 평가 처리량 | > 1000 req/sec (2 replicas) |

---

## ✅ 검수 기준

### 기능 검수

- [ ] OPA 정책 엔진이 Kubernetes에 배포되어 정상 작동
- [ ] 6개 정책 예시가 모두 구현되고 테스트 통과
- [ ] FastAPI 데코레이터가 정상 작동 (정책 거부 시 403 반환)
- [ ] ConfigMap 변경 시 30초 이내 Hot-Reload
- [ ] Prometheus 메트릭이 수집되고 Grafana 대시보드에 표시
- [ ] 정책 위반 시 Slack 알림 전송
- [ ] 단위 테스트 커버리지 80% 이상
- [ ] 통합 테스트 10개 이상 작성 및 통과

### 성능 검수

- [ ] 정책 평가 지연시간 P95 < 50ms
- [ ] 정책 평가 지연시간 P99 < 100ms
- [ ] OPA Pod 메모리 사용량 < 256MB
- [ ] OPA Pod CPU 사용량 < 500m
- [ ] 부하 테스트: 1000 req/sec 처리 가능

### 문서 검수

- [ ] DEPLOYMENT_GUIDE.md 작성 완료 (1,000+ 라인)
- [ ] POLICY_DEVELOPMENT_GUIDE.md 작성 완료 (1,000+ 라인)
- [ ] API_REFERENCE.md 작성 완료 (500+ 라인)
- [ ] MONITORING_GUIDE.md 작성 완료 (800+ 라인)
- [ ] 모든 코드에 docstring 및 주석 포함

---

## 🚀 배포 계획

### Phase 1: 개발 환경 (1주차)

- [ ] OPA Deployment 배포 (dev 환경)
- [ ] 정책 예시 1-2개 구현 및 테스트
- [ ] FastAPI 데코레이터 프로토타입
- [ ] 기본 메트릭 수집

### Phase 2: 스테이징 환경 (2-3주차)

- [ ] 전체 정책 6개 구현
- [ ] FastAPI 통합 완료
- [ ] Grafana 대시보드 구성
- [ ] 알림 규칙 설정
- [ ] 통합 테스트

### Phase 3: 프로덕션 환경 (4주차)

- [ ] 프로덕션 정책 번들 배포
- [ ] HPA 설정 및 부하 테스트
- [ ] 모니터링 검증
- [ ] 문서화 완료
- [ ] 운영팀 교육

---

## 🔗 참고 자료

### 내부 문서

- **POLICY_LAYER_DESIGN.md**: 정책 계층 설계 문서 (3,500+ 라인)
- **GOVERNANCE_IMPLEMENTATION_v2_SUMMARY.md**: 거버넌스 시스템 구현 요약
- **QUICKSTART_SLACK.md**: Slack 알림 설정 가이드
- **SETUP_CREDENTIALS.md**: Slack Webhook 발급 가이드

### 외부 문서

- [Open Policy Agent 공식 문서](https://www.openpolicyagent.org/docs/)
- [Rego 언어 가이드](https://www.openpolicyagent.org/docs/latest/policy-language/)
- [OPA Kubernetes Tutorial](https://www.openpolicyagent.org/docs/latest/kubernetes-tutorial/)
- [FastAPI 공식 문서](https://fastapi.tiangolo.com/)
- [Prometheus 메트릭 타입](https://prometheus.io/docs/concepts/metric_types/)

### 예제 코드

- [OPA HTTP API 예제](https://www.openpolicyagent.org/docs/latest/rest-api/)
- [FastAPI 미들웨어 예제](https://fastapi.tiangolo.com/advanced/middleware/)
- [Prometheus Python 클라이언트](https://github.com/prometheus/client_python)

---

## 💬 질문 사항

구현 중 다음 사항에 대해 질문이나 제안이 있으시면 언제든지 문의해 주세요:

1. **정책 우선순위**: 여러 정책이 충돌할 경우 우선순위 결정 방식
2. **캐싱 전략**: 정책 평가 결과 캐싱 여부 및 TTL
3. **장애 대응**: OPA 서비스 장애 시 Fallback 정책
4. **보안**: 정책 번들 암호화 필요 여부
5. **확장성**: 향후 추가 정책 (예: 지역별 규제 준수) 계획

---

## 📝 진행 상황 보고

구현 중 주요 마일스톤 달성 시 다음 형식으로 보고 부탁드립니다:

```markdown
**날짜**: 2025-11-XX
**Phase**: Phase X - XXX
**완료 항목**:
- [ ] OPA Deployment 배포
- [ ] 정책 예시 3개 구현
- [ ] ...

**진행 중 항목**:
- FastAPI 데코레이터 구현 (70%)
- ...

**이슈**:
- OPA ConfigMap Hot-Reload 지연 (해결 중)
- ...

**다음 주 계획**:
- Grafana 대시보드 구성
- ...
```

---

**요청자**: DreamSeedAI Infrastructure Team  
**검수자**: Won (won@dreamseedai.com)  
**예상 완료일**: 2025-12-06  
**우선순위**: High

---

## 🎯 최종 목표

"교사/학부모가 신뢰하고, 학생이 안전하게 사용할 수 있는 AI 교육 플랫폼"을 구현하기 위해 정책 계층이 실시간으로 AI 행동을 제어하고, 시스템 운영 규칙을 집행하는 **도덕률 집행자** 역할을 수행하도록 구현해 주세요.

감사합니다! 🙏
