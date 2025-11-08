# Governance Kustomize Deployment

**배포 방식**: Kustomize Base + Overlays  
**네임스페이스**: `seedtest` (staging), `seedtest-prod` (production)  
**K8s 버전**: v1.28.0+

---

## 📋 디렉터리 구조

```
ops/k8s/governance/
├── kustomization.yaml              # Base configuration
├── deployment.yaml                 # Backend deployment with governance
├── service.yaml                    # ClusterIP service
├── servicemonitor.yaml             # Prometheus monitoring
├── networkpolicy.yaml              # Network policies
└── overlays/
    ├── phase0/                     # Phase 0: Soft mode (audit only)
    │   ├── kustomization.yaml
    │   └── phase0-patch.yaml
    ├── phase1/                     # Phase 1: Enforce mode (core RBAC)
    │   ├── kustomization.yaml
    │   └── phase1-patch.yaml
    └── prod/                       # Phase 2+: Production (all features)
        ├── kustomization.yaml
        └── prod-patch.yaml
```

---

## 🚀 빠른 배포 (5분)

### Step 1: Policy Bundle 컴파일
```bash
cd /home/won/projects/dreamseed_monorepo
python3 ops/scripts/compile_policy_bundle.py
```

### Step 2: Phase 0 배포 (Soft mode - 관찰만)
```bash
# Dry-run 먼저
DRY_RUN=true bash ops/scripts/deploy_governance_kustomize.sh phase0 seedtest

# 실제 배포
bash ops/scripts/deploy_governance_kustomize.sh phase0 seedtest
```

### Step 3: 검증
```bash
# Deployment 상태
kubectl get deploy backend -n seedtest

# Pod 로그
kubectl logs -f deploy/backend -n seedtest | grep -i governance

# Policy 상태 확인
kubectl exec -it deploy/backend -n seedtest -- \
  curl http://localhost:8000/internal/policy/status | jq
```

### Step 4: 관찰 (24-48시간)
```bash
# Audit 로그 모니터링
kubectl logs -f deploy/backend -n seedtest | grep "SOFT.*violation"

# 위반 패턴 분석
kubectl logs deploy/backend -n seedtest --since=24h | \
  grep "RBAC violation" | \
  awk '{print $NF}' | sort | uniq -c | sort -rn
```

### Step 5: Phase 1 전환 (Enforce mode)
```bash
# 48시간 관찰 후, 문제 없으면 Phase 1로 전환
bash ops/scripts/deploy_governance_kustomize.sh phase1 seedtest
```

---

## 📦 Phase별 차이

### Phase 0 (Soft Mode)
```yaml
env:
  - name: POLICY_BUNDLE_ID
    value: "phase0"
  - name: GOVERNANCE_PHASE
    value: "0"
  - name: POLICY_STRICT_MODE
    value: "soft"  # ← 로그만, 차단 안함
```

**특징**:
- ✅ 모든 요청 허용
- ✅ 위반 시 로그만 기록
- ✅ 성능 영향 최소
- ✅ 패턴 분석 가능

**관찰 지표**:
```bash
# 위반 건수 (TOP 10)
kubectl logs deploy/backend -n seedtest --since=24h | \
  grep "RBAC violation" | \
  awk -F'action=' '{print $2}' | cut -d' ' -f1 | \
  sort | uniq -c | sort -rn | head -10

# 위반 사용자 (TOP 10)
kubectl logs deploy/backend -n seedtest --since=24h | \
  grep "RBAC violation" | \
  awk -F'user=' '{print $2}' | cut -d' ' -f1 | \
  sort | uniq -c | sort -rn | head -10
```

### Phase 1 (Enforce Mode)
```yaml
env:
  - name: POLICY_BUNDLE_ID
    value: "phase1"
  - name: GOVERNANCE_PHASE
    value: "1"
  - name: POLICY_STRICT_MODE
    value: "enforce"  # ← 실제 차단
replicas: 3  # ← 높은 가용성
```

**특징**:
- ✅ RBAC 강제 집행 (403 Forbidden)
- ✅ Feature Flags 체크
- ✅ Teacher 승인 워크플로
- ✅ Audit 로그 DB 저장

**테스트**:
```bash
# Viewer는 POST 차단 (403 예상)
kubectl exec -it deploy/backend -n seedtest -- \
  curl -X POST http://localhost:8000/api/v1/assignments \
    -H "X-Roles: viewer" \
    -H "Content-Type: application/json" \
    -d '{"title":"Test"}'
# Expected: 403 Forbidden

# Teacher는 POST 허용 (200 예상)
kubectl exec -it deploy/backend -n seedtest -- \
  curl -X POST http://localhost:8000/api/v1/assignments \
    -H "X-Roles: teacher" \
    -H "Content-Type: application/json" \
    -d '{"title":"Test"}'
# Expected: 200 OK or 202 Accepted (if approval needed)
```

### Production (Phase 2+)
```yaml
env:
  - name: POLICY_BUNDLE_ID
    value: "prod"
  - name: GOVERNANCE_PHASE
    value: "2"
namespace: seedtest-prod  # ← 별도 네임스페이스
replicas: 5               # ← 높은 처리량
resources:
  limits:
    cpu: "2"
    memory: "4Gi"         # ← 더 큰 리소스
```

**특징**:
- ✅ Risk Engine 활성화
- ✅ Parent Portal 활성화
- ✅ Exam Pipeline 활성화
- ✅ Fairness Monitoring 활성화
- ✅ Org-level Policy Override

---

## 🔧 Hot-Reload (재배포 없이 정책 변경)

### 방법 1: ConfigMap 업데이트 (권장)
```bash
# 1. Policy 수정
vim governance/bundles/policy_bundle_phase1.yaml

# 2. 재컴파일
python3 ops/scripts/compile_policy_bundle.py

# 3. ConfigMap 업데이트
kubectl create configmap governance-bundles \
  --from-file=policy_bundle_phase0.json=governance/compiled/policy_bundle_phase0.json \
  --from-file=policy_bundle_phase1.json=governance/compiled/policy_bundle_phase1.json \
  --from-file=policy_bundle_prod.json=governance/compiled/policy_bundle_prod.json \
  -n seedtest \
  --dry-run=client -o yaml | kubectl apply -f -

# 4. Hot-Reload API 호출 (Pod 재시작 불필요)
kubectl exec -it deploy/backend -n seedtest -- \
  curl -X POST http://localhost:8000/internal/policy/reload

# 5. 확인
kubectl exec -it deploy/backend -n seedtest -- \
  curl http://localhost:8000/internal/policy/status | jq '.version'
```

### 방법 2: Kustomize 재배포 (ConfigMap hash 변경 → 자동 재시작)
```bash
# ConfigMap hash가 변경되면 Pod가 자동 재시작됨
kustomize build ops/k8s/governance/overlays/phase1 | kubectl apply -f -
```

---

## 🧪 테스트 시나리오

### 1. RBAC 테스트
```bash
POD=$(kubectl get pod -n seedtest -l app=backend -o jsonpath='{.items[0].metadata.name}')

# Admin - 모든 액션 허용
kubectl exec -n seedtest $POD -- \
  curl -s http://localhost:8000/internal/policy/reload \
    -H "X-Roles: admin" -X POST
# Expected: 200 OK

# Viewer - POST 차단
kubectl exec -n seedtest $POD -- \
  curl -s http://localhost:8000/api/v1/assignments \
    -H "X-Roles: viewer" -X POST
# Expected: 403 Forbidden

# Teacher - POST 허용
kubectl exec -n seedtest $POD -- \
  curl -s http://localhost:8000/api/v1/assignments \
    -H "X-Roles: teacher" -X POST
# Expected: 200 OK or 202 Accepted
```

### 2. Feature Flag 테스트
```bash
# Risk Engine 비활성화 시 (Phase 0/1)
kubectl exec -n seedtest $POD -- \
  curl -s http://localhost:8000/api/v1/risk/students/123 \
    -H "X-Roles: teacher"
# Expected: 403 Feature disabled (Phase 0/1)
# Expected: 200 OK (Phase 2+/prod)
```

### 3. Health Check
```bash
# Readiness
kubectl exec -n seedtest $POD -- curl -s http://localhost:8000/readyz
# Expected: OK

# Liveness
kubectl exec -n seedtest $POD -- curl -s http://localhost:8000/healthz
# Expected: OK

# Policy Status
kubectl exec -n seedtest $POD -- \
  curl -s http://localhost:8000/internal/policy/status | jq
# Expected: JSON with bundle info
```

---

## 🔄 Phase 전환 전략

### Phase 0 → Phase 1 전환
**조건** (모두 만족 시):
- [ ] 48시간 이상 관찰 완료
- [ ] RBAC 위반 패턴 분석 완료
- [ ] 오탐(false positive) 없음 확인
- [ ] 팀원들에게 정책 공지 완료

**실행**:
```bash
# 1. Phase 1 배포
bash ops/scripts/deploy_governance_kustomize.sh phase1 seedtest

# 2. 즉시 모니터링 (5분)
kubectl logs -f deploy/backend -n seedtest | grep -E "403|Forbidden"

# 3. 문제 발생 시 즉시 롤백
bash ops/scripts/deploy_governance_kustomize.sh phase0 seedtest
```

### Phase 1 → Production 전환
**조건**:
- [ ] 2주 이상 Phase 1 운영 안정
- [ ] DB 마이그레이션 완료 (approval_request, audit_log)
- [ ] Risk Engine 준비 완료
- [ ] Parent Portal 준비 완료

**실행**:
```bash
# 1. Production 네임스페이스 배포
bash ops/scripts/deploy_governance_kustomize.sh prod seedtest-prod

# 2. Traffic 점진적 전환 (Ingress weight)
# 3. 모니터링
```

---

## 📊 모니터링

### Prometheus Metrics (ServiceMonitor 설정됨)
```promql
# Policy 체크 횟수
rate(governance_policy_check_total[5m])

# RBAC 거부 횟수
rate(governance_rbac_denied_total[5m])

# Feature Flag 차단 횟수
rate(governance_feature_disabled_total[5m])
```

### Logs (Loki/CloudWatch)
```bash
# Governance 관련 로그만
kubectl logs -f deploy/backend -n seedtest | grep -i governance

# 위반 로그만
kubectl logs -f deploy/backend -n seedtest | grep -E "violation|Forbidden"

# Hot-reload 이벤트
kubectl logs -f deploy/backend -n seedtest | grep "reloaded"
```

---

## 🛡️ 보안

### NetworkPolicy
- ✅ Ingress: nginx-ingress, Prometheus만 허용
- ✅ Egress: DNS, HTTPS, DB만 허용
- ✅ 동일 namespace 내 통신 허용

### RBAC (K8s)
- ✅ ServiceAccount: `backend-sa` (생성 필요)
- ✅ Role: ConfigMap 읽기, Secrets 읽기
- ✅ RoleBinding: `backend-sa` → Role

---

## 🔗 관련 문서

- **Policy Bundle 편집**: `governance/bundles/policy_bundle_*.yaml`
- **Route Mapping**: `docs/GOVERNANCE_ROUTE_ACTION_MAPPING.md`
- **Deployment Checklist**: `GOVERNANCE_DEPLOYMENT_CHECKLIST.md`
- **Kustomize 공식 문서**: https://kustomize.io/

---

## 🆘 트러블슈팅

### ConfigMap이 마운트되지 않음
```bash
# ConfigMap 존재 확인
kubectl get configmap governance-bundles -n seedtest

# ConfigMap 내용 확인
kubectl describe configmap governance-bundles -n seedtest

# Pod에서 파일 확인
kubectl exec -it deploy/backend -n seedtest -- ls -la /app/governance/compiled/
```

### Policy 로드 실패
```bash
# Pod 로그 확인
kubectl logs deploy/backend -n seedtest | grep -i "policy"

# ConfigMap 재생성
kubectl delete configmap governance-bundles -n seedtest
kustomize build ops/k8s/governance/overlays/phase1 | kubectl apply -f -
```

### RBAC이 작동하지 않음
```bash
# 1. Policy status 확인
kubectl exec -it deploy/backend -n seedtest -- \
  curl http://localhost:8000/internal/policy/status | jq '.rbac.enabled'

# 2. 환경 변수 확인
kubectl exec -it deploy/backend -n seedtest -- env | grep POLICY

# 3. Hot-reload
kubectl exec -it deploy/backend -n seedtest -- \
  curl -X POST http://localhost:8000/internal/policy/reload
```

---

**Last Updated**: 2025-11-08  
**Maintained by**: Platform Engineering Team
