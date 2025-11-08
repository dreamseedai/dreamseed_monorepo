# DreamSeedAI Governance Layer

## 📋 개요

이 디렉토리는 DreamSeedAI의 **거버넌스 계층 구현**을 포함합니다.

거버넌스 문서(철학, 원칙) → 정책 번들(YAML) → 런타임 집행(코드)의 전체 라이프사이클을 관리합니다.

---

## 📁 디렉토리 구조

```
governance/
├── README.md                    # 이 파일
├── docs/                        # 거버넌스 문서 (철학, 설계, 운영)
│   ├── GOVERNANCE_PHILOSOPHY.md
│   ├── GOVERNANCE_LAYER_OPERATIONS.md
│   ├── GOVERNANCE_LAYER_DETAILED.md
│   ├── GOVERNANCE_LAYER_SUMMARY.md
│   └── GOVERNANCE_ROLES_AND_RESPONSIBILITIES.md
├── bundles/                     # 정책 번들 원본 (YAML)
│   ├── policy_bundle_phase0.yaml
│   ├── policy_bundle_phase1.yaml
│   ├── policy_bundle_phase2.yaml
│   └── policy_bundle_prod.yaml
├── compiled/                    # 컴파일된 정책 (JSON, 런타임용)
│   └── policy_bundle_prod.json
├── schemas/                     # JSON Schema (검증용)
│   └── policy-bundle.schema.json
├── scripts/                     # 정책 관리 스크립트
│   ├── compile.py               # YAML → JSON 컴파일
│   ├── validate.py              # Schema 검증
│   └── sign.py                  # 정책 서명 (옵션)
└── tests/                       # 정책 테스트
    └── test_policy_bundles.py
```

---

## 🔑 핵심 개념

### 1. 정책 번들 (Policy Bundle)

거버넌스 문서에서 합의된 규칙을 **기계가 실행할 수 있는 형태**로 변환한 것입니다.

**구성 요소**:
- `bundle_id`: 정책 번들 식별자 (예: `phase1`, `prod-2025-11-06`)
- `phase`: 거버넌스 단계 (0-3)
- `rbac`: 역할 기반 접근 제어 규칙
- `safety`: 안전성 정책 (튜터, 콘텐츠 필터)
- `privacy`: 개인정보 보호 정책
- `approvals`: 승인 워크플로우 규칙
- `feature_flags`: 기능 플래그
- `org_overrides`: 조직별 커스터마이징 허용 여부

### 2. 환경 변수 (설정 키)

런타임은 다음 환경 변수로 정책을 제어합니다:

```bash
# 필수
POLICY_BUNDLE_ID=phase1                    # 적용할 정책 번들
GOVERNANCE_PHASE=1                         # 현재 거버넌스 단계 (0-3)

# 선택
POLICY_STRICT_MODE=enforce                 # soft(경고만) | enforce(강제 차단)
ORG_POLICY_MODE=allow                      # org별 오버라이드 허용 여부
POLICY_BUNDLE_PATH=governance/compiled/policy_bundle_prod.json
```

### 3. 집행 메커니즘

정책은 다음 레이어에서 집행됩니다:

1. **API Gateway/Middleware**: 모든 HTTP 요청에 대해 RBAC, 기능 플래그 검사
2. **Service Hooks**: 서비스 로직 내에서 콘텐츠 필터, 승인 워크플로우 적용
3. **Batch Jobs**: Celery 태스크 시작 시 feature flag 확인
4. **Database**: Row-Level Security로 데이터 접근 제어

---

## 🚀 빠른 시작

### Phase 0: 준비 (현재)

거버넌스 문서 작성 완료 → 정책 번들 스켈레톤 생성

```bash
# 1. 정책 번들 생성
cd governance/bundles
cp policy_bundle_phase0.yaml policy_bundle_phase1.yaml

# 2. 검증
python scripts/validate.py bundles/policy_bundle_phase1.yaml

# 3. 컴파일
python scripts/compile.py bundles/policy_bundle_phase1.yaml -o compiled/policy_bundle_phase1.json
```

### Phase 1: 핵심 거버넌스 활성화

```bash
# 환경 변수 설정
export POLICY_BUNDLE_ID=phase1
export GOVERNANCE_PHASE=1
export POLICY_STRICT_MODE=soft  # 처음엔 경고만

# FastAPI 미들웨어 활성화
# backend/app/main.py에 GovernanceMiddleware 추가
```

### Phase 2: 확장

```bash
export GOVERNANCE_PHASE=2
export POLICY_STRICT_MODE=enforce  # 강제 집행
export ORG_POLICY_MODE=allow       # org별 커스터마이징 허용
```

---

## 📊 거버넌스 대시보드

거버넌스 대시보드(`/dashboards/governance-admin/`)에서 다음을 관리합니다:

1. **정책 번들 스위처**: 현재 적용 중인 번들 선택/변경
2. **RBAC 매트릭스**: 역할별 권한 시각화
3. **기능 플래그 콘솔**: 기능 on/off 토글
4. **승인 큐**: 대기 중인 승인 요청 처리
5. **감사 로그**: 정책 위반, 차단, 승인 이력 조회

---

## 🔄 워크플로우

### 정책 변경 프로세스

1. **제안**: 거버넌스 위원회에서 정책 변경 논의
2. **문서화**: `docs/` 문서 업데이트
3. **번들 수정**: `bundles/*.yaml` 수정
4. **검증**: `scripts/validate.py`로 JSON Schema 검증
5. **PR**: GitHub PR 생성 → 코드 리뷰
6. **승인**: 거버넌스 위원회 승인
7. **컴파일**: `scripts/compile.py`로 JSON 생성
8. **배포**: `compiled/*.json`을 포함한 릴리즈
9. **적용**: 환경 변수로 활성화 또는 대시보드에서 hot reload

### 긴급 정책 변경

```bash
# 1. 대시보드에서 즉시 플래그 변경 (예: 기능 긴급 비활성화)
# 2. 감사 로그 자동 기록
# 3. 사후 거버넌스 위원회 승인
```

---

## 🧪 테스트

```bash
# 정책 번들 검증 테스트
pytest governance/tests/test_policy_bundles.py

# RBAC 테스트
pytest backend/tests/test_governance_rbac.py

# 기능 플래그 테스트
pytest backend/tests/test_feature_flags.py

# End-to-End 테스트
pytest backend/tests/test_governance_e2e.py
```

---

## 📦 배포

### Docker 이미지에 정책 포함

```dockerfile
# Dockerfile
FROM python:3.11

# 정책 번들 복사
COPY governance/compiled/policy_bundle_prod.json /app/governance/

ENV POLICY_BUNDLE_PATH=/app/governance/policy_bundle_prod.json
ENV POLICY_BUNDLE_ID=prod-2025-11-06
```

### Kubernetes ConfigMap

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: governance-policy
data:
  policy_bundle_prod.json: |
    {
      "bundle_id": "prod-2025-11-06",
      "phase": 2,
      ...
    }
```

---

## 📝 주요 파일 설명

### `bundles/policy_bundle_phase1.yaml`

Phase 1에 적용할 정책 번들. RBAC, 안전성, 기본 승인 워크플로우 포함.

### `compiled/policy_bundle_prod.json`

프로덕션 환경에서 사용할 컴파일된 정책. 런타임이 읽는 최종 형태.

### `schemas/policy-bundle.schema.json`

정책 번들의 JSON Schema. 검증에 사용.

### `scripts/compile.py`

YAML → JSON 변환 + 검증 + 서명(옵션)

---

## 🔒 보안

- **정책 서명**: 프로덕션 정책은 서명하여 무결성 보장 (옵션)
- **접근 제어**: 정책 파일 수정은 거버넌스 위원회만 가능
- **감사 로그**: 모든 정책 변경 이력 기록
- **버전 관리**: Git으로 정책 변경 추적

---

## 🛠️ 개발 가이드

### 새로운 정책 규칙 추가

1. `bundles/policy_bundle_*.yaml`에 규칙 추가
2. `schemas/policy-bundle.schema.json`에 스키마 정의
3. `backend/app/policy/` 모듈에 집행 로직 구현
4. 테스트 작성
5. 문서 업데이트

### 새로운 기능 플래그 추가

1. `bundles/*.yaml`의 `feature_flags`에 플래그 추가
2. 코드에서 `feature_enabled()` 호출
3. 대시보드에 토글 UI 추가

---

## 📚 관련 문서

- [거버넌스 철학](./docs/GOVERNANCE_PHILOSOPHY.md)
- [거버넌스 운영](./docs/GOVERNANCE_LAYER_OPERATIONS.md)
- [역할과 책임](./docs/GOVERNANCE_ROLES_AND_RESPONSIBILITIES.md)
- [4계층 아키텍처](../docs/architecture/4_LAYER_ARCHITECTURE.md)

---

## 🤝 기여

거버넌스 정책 변경은 다음 프로세스를 따릅니다:

1. 이슈 생성 (정책 변경 제안)
2. 거버넌스 위원회 논의
3. PR 제출 (문서 + 번들)
4. 코드 리뷰 + 위원회 승인
5. 머지 및 배포

---

**Last Updated**: 2025-11-07  
**Version**: 1.0.0  
**Owner**: DreamSeedAI Governance Board
