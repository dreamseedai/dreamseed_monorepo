# ArgoCD App-of-Apps Pattern

이 디렉토리는 ArgoCD의 App-of-Apps 패턴을 구현합니다.

## 구조

```
infra/argocd/
├── app-of-apps.yaml          # Root Application (모든 앱을 관리)
├── apps/
│   └── r-plumber.yaml         # R GLMM Analytics Service
└── README.md                  # 이 파일
```

## 배포 방법

### 1. App-of-Apps 배포

```bash
# ArgoCD에 Root Application 등록
kubectl apply -f infra/argocd/app-of-apps.yaml

# 상태 확인
kubectl get applications -n argocd
```

이렇게 하면 `apps/` 디렉토리의 모든 Application이 자동으로 등록됩니다.

### 2. 개별 앱 배포 (수동)

```bash
# R Plumber만 배포
kubectl apply -f infra/argocd/apps/r-plumber.yaml
```

## ArgoCD UI 접근

```bash
# Port forward
kubectl port-forward svc/argocd-server -n argocd 8080:443

# Admin 비밀번호 확인
kubectl -n argocd get secret argocd-initial-admin-secret \
  -o jsonpath="{.data.password}" | base64 -d
```

https://localhost:8080 에서 접속

## 새 앱 추가 방법

1. `ops/k8s/your-app/` 에 K8s 매니페스트 생성
2. `infra/argocd/apps/your-app.yaml` 생성:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: your-app
  namespace: argocd
  labels:
    app.kubernetes.io/part-of: dreamseed
spec:
  project: default
  source:
    repoURL: https://github.com/dreamseedai/dreamseed_monorepo.git
    targetRevision: HEAD
    path: ops/k8s/your-app
  destination:
    server: https://kubernetes.default.svc
    namespace: your-namespace
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
```

3. Git push하면 자동으로 ArgoCD가 감지하고 배포

## Sync Policy

- **automated**: 자동 동기화 활성화
- **prune**: Git에서 삭제된 리소스 자동 제거
- **selfHeal**: 클러스터에서 수동 변경된 리소스 자동 복구

## 문제 해결

### 앱이 동기화되지 않을 때

```bash
# 수동 sync
argocd app sync r-glmm-plumber

# 또는 UI에서 "Sync" 버튼 클릭
```

### 앱 삭제

```bash
# Application 제거 (리소스도 함께 삭제)
kubectl delete application r-glmm-plumber -n argocd

# Application만 제거 (리소스는 유지)
kubectl patch application r-glmm-plumber -n argocd \
  --type json -p='[{"op": "remove", "path": "/metadata/finalizers"}]'
kubectl delete application r-glmm-plumber -n argocd
```

