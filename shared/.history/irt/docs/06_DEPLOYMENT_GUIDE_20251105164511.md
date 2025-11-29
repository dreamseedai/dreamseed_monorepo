# Deployment Guide

Document: 06_DEPLOYMENT_GUIDE.md
Part of: IRT System Documentation Series
Created: 2025-11-05
Status: ✅ Production Ready

---

## Overview

This guide provides an end-to-end deployment playbook for the IRT system across environments (local, staging, production) covering database migrations, calibration workers (PyMC, brms), scheduled automation (Kubernetes CronJobs, SystemD timers), API, and frontend wiring.

What you’ll deploy:
- Database schema in schema "shared_irt"
- Calibration engines (PyMC in Python, brms in R)
- API endpoints (FastAPI) with JWT auth
- Monthly report generator (PDF)
- Drift alerts automation
- React dashboard integration

---

## Prerequisites Checklist

- PostgreSQL 12+ with extensions enabled: uuid-ossp, pgcrypto
- Python 3.10+ (uvicorn, fastapi, sqlalchemy, alembic, pymc, arviz)
- R 4.2+ with cmdstanr or rstan, brms installed
- Docker 24+, kubectl 1.27+, helm (optional)
- SystemD (for on-prem or VM deployments)
- Nginx or ALB ingress for HTTPS
- Domain and TLS certificate (Let’s Encrypt or ACM)
- S3 bucket (optional) for report storage

---

## Environment Configuration

Recommended environment variables (example):

```bash
# Database
POSTGRES_HOST=postgres.internal
POSTGRES_PORT=5432
POSTGRES_DB=dreamseed
POSTGRES_USER=portal
POSTGRES_PASSWORD=********

# API
API_BIND=0.0.0.0
API_PORT=8000
JWT_SECRET=change_me_strong_secret
JWT_EXPIRES_IN=3600
CORS_ORIGINS=http://localhost:5173,https://portal.dreamseedai.com

# Calibration
IRT_CALIBRATION_METHOD=pymc   # pymc|brms|mirt
IRT_MODEL=3PL                 # 2PL|3PL
IRT_WINDOW_START=2024-10-01
IRT_WINDOW_END=2024-10-31

# Reports
REPORT_OUTPUT_DIR=/var/irt/reports
S3_BUCKET=irt-reports
S3_PREFIX=monthly/
AWS_REGION=ap-northeast-2

# Observability
LOG_LEVEL=INFO
SENTRY_DSN=
```

Kubernetes secrets example:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: irt-secrets
  namespace: portal
type: Opaque
data:
  POSTGRES_PASSWORD: <base64>
  JWT_SECRET: <base64>
  SENTRY_DSN: <base64>
```

SystemD environment file example:

```bash
# /etc/irt/irt.env
POSTGRES_HOST=127.0.0.1
POSTGRES_DB=dreamseed
POSTGRES_USER=portal
POSTGRES_PASSWORD=supersecret
JWT_SECRET=very_strong_secret
REPORT_OUTPUT_DIR=/var/irt/reports
```

---

## Database Migration

Migration file: `apps/seedtest_api/alembic/versions/20251105_1400_shared_irt_init.py`

1) Configure alembic.ini (sqlalchemy.url) or environment variables.

2) Run migration:

```bash
# From apps/seedtest_api/
alembic upgrade head
```

3) Verify schema:

```sql
SELECT table_schema, table_name
FROM information_schema.tables
WHERE table_schema='shared_irt'
ORDER BY table_name;
```

4) Seed minimal metadata (optional):

```sql
INSERT INTO shared_irt.windows (window_id, window_start, window_end, created_at)
VALUES (1, '2024-10-01', '2024-10-31', now());
```

Rollback:

```bash
alembic downgrade -1
```

---

## Docker Images

Build recommended images.

### 1) PyMC calibration worker

```dockerfile
# Dockerfile.pymc
FROM python:3.11-slim
RUN pip install --no-cache-dir numpy scipy pandas pymc arviz sqlalchemy psycopg2-binary click jinja2 weasyprint
WORKDIR /app
COPY shared/ /app/shared/
COPY apps/seedtest_api/ /app/apps/seedtest_api/
ENV PYTHONUNBUFFERED=1
ENTRYPOINT ["python", "-m", "apps.seedtest_api.app.calibration_pymc_cli"]
```

Build & push:

```bash
docker build -f Dockerfile.pymc -t ghcr.io/dreamseedai/irt-calibration-pymc:2025-11-05 .
docker push ghcr.io/dreamseedai/irt-calibration-pymc:2025-11-05
```

### 2) brms calibration worker (R/Stan)

Use `portal_front/r-plumber/Dockerfile` as a starting point if available. Example:

```dockerfile
# Dockerfile.brms
FROM rocker/r-ver:4.3.1
RUN R -e "install.packages(c('cmdstanr','brms','RPostgres','dplyr'), repos='https://cloud.r-project.org')"
RUN R -e "cmdstanr::install_cmdstan()"
WORKDIR /app
COPY portal_front/r-plumber/ /app/r-plumber/
ENTRYPOINT ["Rscript", "/app/r-plumber/calibration_brms.R"]
```

Build & push:

```bash
docker build -f Dockerfile.brms -t ghcr.io/dreamseedai/irt-calibration-brms:2025-11-05 .
docker push ghcr.io/dreamseedai/irt-calibration-brms:2025-11-05
```

---

## Kubernetes Deployment (Cloud)

### Namespaces and RBAC

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: portal
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: irt-sa
  namespace: portal
```

### ConfigMap & Secret

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: irt-config
  namespace: portal
data:
  API_PORT: "8000"
  IRT_MODEL: "3PL"
---
apiVersion: v1
kind: Secret
metadata:
  name: irt-secrets
  namespace: portal
type: Opaque
data:
  POSTGRES_PASSWORD: <base64>
  JWT_SECRET: <base64>
```

### API Deployment and Service

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: irt-api
  namespace: portal
spec:
  replicas: 2
  selector:
    matchLabels: { app: irt-api }
  template:
    metadata:
      labels: { app: irt-api }
    spec:
      serviceAccountName: irt-sa
      containers:
        - name: api
          image: ghcr.io/dreamseedai/portal-api:latest
          ports: [{ containerPort: 8000 }]
          env:
            - name: POSTGRES_HOST
              value: postgres.portal.svc
            - name: POSTGRES_DB
              value: dreamseed
            - name: POSTGRES_USER
              value: portal
            - name: POSTGRES_PASSWORD
              valueFrom:
                secretKeyRef: { name: irt-secrets, key: POSTGRES_PASSWORD }
            - name: JWT_SECRET
              valueFrom:
                secretKeyRef: { name: irt-secrets, key: JWT_SECRET }
          resources:
            requests: { cpu: "200m", memory: "256Mi" }
            limits:   { cpu: "1", memory: "512Mi" }
---
apiVersion: v1
kind: Service
metadata:
  name: irt-api
  namespace: portal
spec:
  selector: { app: irt-api }
  ports:
    - port: 80
      targetPort: 8000
```

### Ingress (Nginx)

See `infra/nginx/` for security headers and rate limit examples.

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: irt-api
  namespace: portal
  annotations:
    nginx.ingress.kubernetes.io/proxy-body-size: "10m"
    nginx.ingress.kubernetes.io/server-snippet: |
      include /etc/nginx/snippets/security_headers.conf;
spec:
  ingressClassName: nginx
  tls:
    - hosts: [api.dreamseedai.com]
      secretName: api-tls
  rules:
    - host: api.dreamseedai.com
      http:
        paths:
          - path: /api/irt
            pathType: Prefix
            backend:
              service:
                name: irt-api
                port: { number: 80 }
```

### CronJobs (Monthly Calibration & Reports)

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: irt-calibration-monthly
  namespace: portal
spec:
  schedule: "0 2 1 * *"   # At 02:00 on day-of-month 1
  successfulJobsHistoryLimit: 1
  failedJobsHistoryLimit: 2
  jobTemplate:
    spec:
      backoffLimit: 1
      template:
        spec:
          restartPolicy: Never
          containers:
            - name: calibrate
              image: ghcr.io/dreamseedai/irt-calibration-pymc:2025-11-05
              envFrom:
                - configMapRef: { name: irt-config }
                - secretRef: { name: irt-secrets }
              resources:
                requests: { cpu: "1", memory: "2Gi" }
                limits:   { cpu: "4", memory: "8Gi" }
---
apiVersion: batch/v1
kind: CronJob
metadata:
  name: irt-report-monthly
  namespace: portal
spec:
  schedule: "0 3 1 * *"   # After calibration
  jobTemplate:
    spec:
      template:
        spec:
          restartPolicy: Never
          containers:
            - name: report
              image: ghcr.io/dreamseedai/irt-calibration-pymc:2025-11-05
              command: ["python", "-m", "apps.seedtest_api.app.generate_report_cli"]
              envFrom:
                - configMapRef: { name: irt-config }
                - secretRef: { name: irt-secrets }
```

---

## SystemD Deployment (On‑prem/VM)

Use templates in `infra/systemd/`.

### Install services

```bash
# Copy example files and edit paths
sudo cp infra/systemd/irt-calibration.service.example /etc/systemd/system/irt-calibration.service
sudo cp infra/systemd/irt-calibration.timer /etc/systemd/system/irt-calibration.timer
sudo cp infra/systemd/irt-report.service.example /etc/systemd/system/irt-report.service
sudo cp infra/systemd/irt-report.timer /etc/systemd/system/irt-report.timer

# Environment file
sudo mkdir -p /etc/irt
sudo cp infra/systemd/README.md /etc/irt/README.md
sudo nano /etc/irt/irt.env

# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable --now irt-calibration.timer
sudo systemctl enable --now irt-report.timer

# Run ad-hoc
sudo systemctl start irt-calibration.service
sudo systemctl status irt-calibration.service
journalctl -u irt-calibration.service -f
```

Security hardening (examples already in templates):
- NoNewPrivileges=true, PrivateTmp=true, ProtectSystem=strict, ReadWritePaths=/var/irt
- User=irt, Group=irt, CapabilityBoundingSet=, ProtectHome=true

---

## Frontend (Portal) Wiring

Build deployment for `portal_front` (Vite):

```bash
cd portal_front
npm ci
npm run build
# Output: dist/
```

Serve with Nginx:

```nginx
server {
  listen 443 ssl http2;
  server_name portal.dreamseedai.com;

  include /etc/nginx/snippets/security_headers.conf;

  root /var/www/portal_front/dist;
  index index.html;

  location /api/ {
    proxy_pass https://api.dreamseedai.com/;
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
  }
}
```

---

## Verification & Smoke Tests

1) API health
```bash
curl -sSf https://api.dreamseedai.com/api/irt/health
```

2) OpenAPI docs
- https://api.dreamseedai.com/docs

3) Drift summary (with token)
```bash
curl -H "Authorization: Bearer $TOKEN" \
  https://api.dreamseedai.com/api/irt/drift/summary | jq .
```

4) Calibration job started (K8s)
```bash
kubectl -n portal get jobs | grep irt-calibration
kubectl -n portal logs job/irt-calibration-monthly-xxxx
```

5) Reports exist
```bash
ls -lh /var/irt/reports
# Or
aws s3 ls s3://$S3_BUCKET/$S3_PREFIX
```

6) Frontend loads dashboard
- Visit https://portal.dreamseedai.com/admin/irt/drift

---

## Rollback Procedures

Database:
```bash
alembic downgrade -1
```

API/Workers (K8s):
```bash
kubectl -n portal rollout undo deployment/irt-api
kubectl -n portal delete job -l job-name=irt-calibration-monthly --force --grace-period=0
```

SystemD:
```bash
sudo systemctl stop irt-calibration.timer
sudo systemctl stop irt-calibration.service
# Revert /etc/irt/irt.env and restart
```

Frontend:
- Revert Nginx symlink to previous build
- Purge CDN cache if used

---

## Monitoring & Observability

Logs:
- API: `kubectl -n portal logs deploy/irt-api -f`
- Jobs: `kubectl -n portal logs job/<name>`
- SystemD: `journalctl -u irt-* -f`

Metrics:
- Add Prometheus scrape annotations to API pods
- Export calibration durations and item counts

Alerts:
- Alert when CronJob fails > 0 in last 24h
- Alert when drift critical alerts > threshold

Sentry:
- Set SENTRY_DSN to capture exceptions in API and workers

---

## Security Considerations

- Use least-privilege DB role for IRT (read/write only shared_irt schema)
- Rotate JWT secret and DB password periodically
- Enable TLS everywhere (Ingress/ALB)
- Configure Nginx rate limits (see `infra/nginx/rate_limit.conf`)
- Validate file outputs and sanitize report inputs

---

## Appendix: Runbooks

### Re-run last calibration (K8s)
```bash
kubectl -n portal create job --from=cronjob/irt-calibration-monthly irt-calibration-manual-$(date +%s)
```

### Manually generate monthly report
```bash
kubectl -n portal create job --from=cronjob/irt-report-monthly irt-report-manual-$(date +%s)
```

### Rotate secrets
```bash
echo -n 'new_secret' | base64
kubectl -n portal patch secret irt-secrets --type=json \
  -p='[{"op":"replace","path":"/data/JWT_SECRET","value":"bmV3X3NlY3JldA=="}]'
```

---

## 한글 요약 (Korean Quick Guide)

배포 항목:
- DB 마이그레이션 실행 (`alembic upgrade head`)
- PyMC/brms 워커 도커 이미지 빌드 & 푸시
- K8s 배포: `Deployment`, `Service`, `Ingress`, `CronJob`
- SystemD 타이머(온프레미스) 설치 및 활성화
- 프론트엔드 빌드 후 Nginx 서빙

검증 체크리스트:
- `/api/irt/health` 200 응답
- 드리프트 요약 API 응답 정상
- CronJob 성공 로그 확인
- 리포트 파일 생성 확인 (로컬/S3)
- 대시보드 페이지 렌더링 확인

롤백:
- Alembic `downgrade -1`
- `rollout undo deployment/irt-api`
- SystemD 서비스 중지 및 환경 복원

보안:
- 최소 권한 DB 계정
- JWT/DB 비밀 주기적 교체
- HTTPS 강제, Nginx 속도 제한 적용

---

Author: DreamSeed AI Team
Last Updated: 2025-11-05
Related: 01_IMPLEMENTATION_REPORT.md, 03_DRIFT_DETECTION_GUIDE.md, 04_API_INTEGRATION_GUIDE.md
