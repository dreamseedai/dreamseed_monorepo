# GCP Workload Identity Federation (OIDC) for GitHub Actions

목표: GitHub Actions → GCP로 서비스 계정 키 없이 인증/배포.

## 0) 전제
- GCP Project: `YOUR_GCP_PROJECT_ID`
- 지역/존: 예) `asia-northeast3`
- 리소스(예시): GKE 클러스터 `dreamseed-cluster` (또는 Cloud Run)
- Org/Repo: `dreamseedai/dreamseed_monorepo`

## 1) Workload Identity Pool & Provider 생성
```bash
gcloud iam workload-identity-pools create gh-pool \
  --project=YOUR_GCP_PROJECT_ID \
  --location="global" \
  --display-name="GitHub Actions Pool"

gcloud iam workload-identity-pools providers create-oidc gh-provider \
  --project=YOUR_GCP_PROJECT_ID \
  --location="global" \
  --workload-identity-pool="gh-pool" \
  --display-name="GitHub OIDC Provider" \
  --issuer-uri="https://token.actions.githubusercontent.com" \
  --attribute-mapping="google.subject=assertion.sub,attribute.repository=assertion.repository,attribute.ref=assertion.ref"
```

## 2) 배포용 서비스 계정 만들기 & 권한 부여
```bash
SA=gha-deployer
PROJECT=YOUR_GCP_PROJECT_ID

gcloud iam service-accounts create $SA \
  --project=$PROJECT \
  --display-name="GitHub Actions Deployer"

# 최소 권한 원칙에 따라 필요한 역할만 부여 (예시: GKE + Artifact Registry)
gcloud projects add-iam-policy-binding $PROJECT \
  --member="serviceAccount:${SA}@${PROJECT}.iam.gserviceaccount.com" \
  --role="roles/container.admin"

gcloud projects add-iam-policy-binding $PROJECT \
  --member="serviceAccount:${SA}@${PROJECT}.iam.gserviceaccount.com" \
  --role="roles/artifactregistry.writer"
```

## 3) GitHub ↔ GCP 트러스트 연결
GitHub 리포에서만 신뢰하도록 WIF 바인딩(Subject: `repo:OWNER/REPO:ref:refs/heads/main` 같은 패턴).

```bash
POOL_ID=$(gcloud iam workload-identity-pools describe gh-pool --project=$PROJECT --location=global --format='value(name)')
PROVIDER_ID=$(gcloud iam workload-identity-pools providers describe gh-provider --project=$PROJECT --location=global --workload-identity-pool=gh-pool --format='value(name)')

# main 브랜치/해당 리포만 허용(필요에 따라 패턴 추가)
gcloud iam service-accounts add-iam-policy-binding ${SA}@${PROJECT}.iam.gserviceaccount.com \
  --project=$PROJECT \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/${POOL_ID}/attribute.repository=dreamseedai/dreamseed_monorepo"
```

브랜치 제한을 강화하려면 `attribute.ref=refs/heads/main` 조건을 provider 측 규칙에 추가하세요.

## 4) GitHub Actions에서 사용 (샘플)

`.github/workflows/deploy-gke.yml`:

```yaml
name: Deploy (GKE)

on:
  workflow_dispatch:
  push:
    branches: [ "main" ]

permissions:
  contents: read
  id-token: write  # 중요: OIDC 토큰 요청 허용

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - id: auth
        uses: google-github-actions/auth@v2
        with:
          workload_identity_provider: "projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/gh-pool/providers/gh-provider"
          service_account: "gha-deployer@YOUR_GCP_PROJECT_ID.iam.gserviceaccount.com"

      - uses: google-github-actions/setup-gcloud@v2

      # GKE 배포 예시
      - name: GKE auth
        run: |
          gcloud container clusters get-credentials dreamseed-cluster --region asia-northeast3 --project YOUR_GCP_PROJECT_ID

      - name: Deploy
        run: |
          kubectl apply -f k8s/  # 예시 경로
```

Cloud Run 예시:

```yaml
      - name: Deploy Cloud Run
        run: |
          gcloud run deploy dreamseed-api \
            --source . \
            --region asia-northeast3 \
            --project YOUR_GCP_PROJECT_ID \
            --allow-unauthenticated
```

## 5) 보안 체크리스트
- GitHub 워크플로 `permissions.id-token: write` 필수
- WIF 바인딩은 리포/브랜치 한정 (`attribute.repository` / `attribute.ref`)
- 불필요 권한은 부여하지 않기(최소 권한 원칙)
- 감사/로깅: 배포 로그를 GCP Cloud Logging/BigQuery로 수집

> `PROJECT_NUMBER`는 `gcloud projects describe YOUR_GCP_PROJECT_ID --format='value(projectNumber)'`로 조회하세요.
