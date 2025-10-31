# GitHub Actions Workflows

이 디렉토리에는 프로젝트의 CI/CD 워크플로가 포함되어 있습니다.

## 주요 워크플로

### k8s-validate.yml

**K8s Kustomize & Kubeconform Validate** - Kubernetes 매니페스트 검증 워크플로

#### 트리거
- `ops/k8s/**` 경로 변경 시 `push` 또는 `pull_request`에서 자동 실행
- 워크플로 파일 자체 변경 시에도 실행

#### 주요 기능

1. **Kustomize 빌드 및 검증**
   - Matrix 전략으로 다음 타깃들을 병렬 검증:
     - `ops/k8s/r-plumber`
     - `ops/k8s/r-plumber/overlays/internal`
     - `ops/k8s/r-irt-plumber`
     - `ops/k8s/r-irt-plumber/overlays/internal`
     - `ops/k8s/cron`

2. **Kubeconform 스키마 검증**
   - Kubernetes v1.28.0 스키마 기준 검증
   - CRD 스키마 레지스트리 사용 (ServiceMonitor, ExternalSecret, Argo Application 등)
   - 렌더된 YAML을 artifact로 업로드

3. **Conftest 정책 검증**
   - `validate` job 성공 후 실행
   - `policy/k8s/*.rego` 정책 파일 적용
   - 배포 보안 및 베스트 프랙티스 검증

4. **ArgoCD Application 검증**
   - `ops/argocd/apps/*.yaml` 파일들에 대한 스키마 검증

#### 사용 방법

**PR에서 자동 실행:**
1. `ops/k8s/**` 경로의 파일을 변경하여 PR 생성
2. "K8s Kustomize & Kubeconform Validate" 워크플로가 자동 실행
3. Actions 탭에서 각 타깃별 빌드/검증 로그 확인
4. 실패 시 로그를 기반으로 매니페스트 수정
5. 렌더된 YAML은 Artifacts에서 다운로드 가능

**로컬에서 테스트:**
```bash
# Kustomize 빌드
kubectl kustomize ops/k8s/r-irt-plumber

# Kubeconform 검증 (Docker 사용)
docker run --rm -v $(pwd):/data ghcr.io/yannh/kubeconform:latest \
  -kubernetes-version v1.28.0 /data/ops/k8s/r-irt-plumber/rendered.yaml

# Conftest 정책 검증
conftest test rendered.yaml -p policy/k8s
```

#### Artifacts

각 타깃별로 렌더된 YAML이 artifact로 저장됩니다:
- `rendered-ops/k8s/r-plumber`
- `rendered-ops/k8s/r-plumber/overlays/internal`
- `rendered-ops/k8s/r-irt-plumber`
- `rendered-ops/k8s/r-irt-plumber/overlays/internal`
- `rendered-ops/k8s/cron`

#### 확장 가능성

- **새 컴포넌트 추가**: `matrix.target`에 다른 경로 추가
- **스키마 레지스트리 커스터마이징**: `CRD_SCHEMA_REGISTRY` 환경 변수 수정
- **정책 추가**: `policy/k8s/*.rego` 파일 추가
- **Kyverno/OPA Gatekeeper**: 정책 검증 단계 추가 가능

### 다른 워크플로

- `ci.yml`: 메인 CI 파이프라인
- `build-seedtest-api.yml`: seedtest-api 빌드
- `backend-seedtest_api-ci-cd.yml`: 백엔드 CI/CD
- `seedtest-api-e2e-smoke.yml`: E2E 스모크 테스트
- 기타 프로젝트별 워크플로

## 정책 파일

`policy/k8s/` 디렉토리에 Rego 정책 파일들이 있습니다:

- `labels.rego`: 필수 라벨 검증
- `deployment_probes.rego`: Deployment 프로브 검증
- `deployment_resources.rego`: 리소스 제한 검증
- `networkpolicy_ingress.rego`: NetworkPolicy 인그레스 규칙 검증
- `service_clusterip.rego`: Service 타입 검증
- `servicemonitor_label.rego`: ServiceMonitor 라벨 검증
- `namespace.rego`: 네임스페이스 검증

## 참고

- [Kustomize 문서](https://kustomize.io/)
- [Kubeconform 문서](https://github.com/yannh/kubeconform)
- [Conftest 문서](https://www.conftest.dev/)

