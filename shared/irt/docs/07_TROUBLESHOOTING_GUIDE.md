# Troubleshooting Guide

Document: 07_TROUBLESHOOTING_GUIDE.md
Part of: IRT System Documentation Series
Created: 2025-11-05
Status: ✅ Production Ready

---

## Contents

1. Quick Diagnostic Flow
2. Database Issues
3. API Issues
4. Calibration Workers (mirt / brms / PyMC)
5. Reports & PDF Generation
6. Frontend (React/Next.js)
7. Kubernetes (Cloud)
8. SystemD (On‑prem/VM)
9. Monitoring & Logs
10. Known Errors & Fixes
11. 한글 빠른 진단 (Korean Quick Guide)

---

## 1) Quick Diagnostic Flow

Follow this when something is broken.

```
Is the API up? (health)
 ├─ No → Check API logs → DB connectivity → Alembic migrated?
 └─ Yes
     ├─ Calibration failing?
     │   ├─ K8s CronJob logs or journalctl (SystemD)
     │   └─ Memory/CPU limits, package versions
     ├─ Reports failing?
     │   ├─ WeasyPrint deps (fonts, pango) / permissions
     │   └─ S3 credentials/region
     └─ Frontend errors?
         ├─ CORS / base URL / env vars
         └─ Token / 401 / rate limit
```

Minimal checks:
- API: GET /api/irt/health → 200
- DB: SELECT 1; from the API pod/container
- Windows exist: SELECT count(*) FROM shared_irt.windows;
- Alerts exist: SELECT count(*) FROM shared_irt.drift_alerts;

---

## 2) Database Issues

### 2.1 Cannot connect to DB

Symptoms:
- API 500 with connection errors
- `psycopg2.OperationalError: could not connect to server`

Checklist:
- POSTGRES_HOST/PORT/DB/USER/PASSWORD set correctly
- Network path open (K8s Service or security group)
- Verify credentials with psql from the same network

```bash
psql "host=$POSTGRES_HOST dbname=$POSTGRES_DB user=$POSTGRES_USER password=$POSTGRES_PASSWORD" -c 'SELECT 1;'
```

Fixes:
- Update env/secrets in Deployment or SystemD EnvironmentFile
- Rotate password and update Secret

---

### 2.2 Alembic migration fails

Symptoms:
- `permission denied for schema shared_irt`
- `relation shared_irt.items does not exist`

Checklist:
- Role has CREATE on schema or run as owner
- Search path includes `shared_irt` where expected
- Alembic points to the correct DB

Fixes:
```sql
CREATE SCHEMA IF NOT EXISTS shared_irt AUTHORIZATION portal;
GRANT USAGE, CREATE ON SCHEMA shared_irt TO portal;
```

Re-run:
```bash
alembic upgrade head
```

---

### 2.3 Slow queries / timeouts

Symptoms:
- `/drift/alerts` or `/items/*/history` slow

Checklist:
- Index btree present on (item_id, window_id), timestamps
- Run EXPLAIN ANALYZE
- VACUUM (ANALYZE) after bulk loads

Fixes:
```sql
ANALYZE shared_irt.item_calibration;
REINDEX INDEX CONCURRENTLY idx_item_calibration_item_window;
```

---

## 3) API Issues

### 3.1 401/403 Unauthorized

Symptoms:
- `detail: Not authenticated`

Checklist:
- Login endpoint works; token present in Authorization header
- Clock skew < 2 min (JWT expiry can be sensitive)
- CORS allows origin of your frontend

Fix:
- Refresh token; ensure `Authorization: Bearer <token>`
- Add allowed origin in CORS middleware

---

### 3.2 404 Not Found (Ingress)

Symptoms:
- `/api/irt/*` returns 404 via Ingress, works internally

Checklist:
- Ingress path prefix `/api/irt` matches app prefix
- No missing trailing slash rewrite

Fix (example annotation):
```yaml
nginx.ingress.kubernetes.io/rewrite-target: /$1
```

---

### 3.3 429 Rate Limited

Fix:
- Honor X-RateLimit headers and backoff
- Batch requests, increase limit per team policy

---

### 3.4 500 Internal Server Error

Checklist:
- Check API logs for Pydantic validation errors
- DB connectivity and migration state

Fix:
- Validate payloads; match models; run migration

---

## 4) Calibration Workers

### 4.1 PyMC OOMKilled / MemoryError

Symptoms:
- K8s pod OOMKilled; Python MemoryError

Fixes:
- Reduce `draws/tune/chains` (e.g., 1000/500/2)
- Increase resources (memory: 4–8Gi)
- Batch items (e.g., 200 at a time)
- Use `return_inferencedata=False` then convert

---

### 4.2 brms divergences or toolchain errors

Symptoms:
- `X divergent transitions after warmup`
- `cmdstanr not found` / toolchain missing

Fixes:
- `adapt_delta=0.99`, `max_treedepth=15`
- Install cmdstan via `cmdstanr::install_cmdstan()`
- Ensure `make`, `gcc` present in image

---

### 4.3 mirt non-convergence

Fixes:
- Increase iterations (max_iter=500)
- Switch to 2PL if c unstable
- Filter items with < 30 responses
- Seed with prior estimates where possible

---

## 5) Reports & PDF

### 5.1 WeasyPrint blank PDF or error

Checklist:
- System packages installed: pango, cairo, libffi, fonts
- Base URL provided so relative paths resolve
- Font availability for CJK (Noto Sans CJK)

Fix (Debian base):
```bash
apt-get update && apt-get install -y libpango-1.0-0 libcairo2 libffi8 fonts-noto-cjk
```

Code:
```python
HTML(string=html, base_url=str(Path(templates_dir))).write_pdf(out_path)
```

---

### 5.2 S3 upload failure

Symptoms:
- `AccessDenied`, `SignatureDoesNotMatch`

Checklist:
- AWS credentials, region match
- Bucket policy allows PutObject
- Correct path/prefix

Fix:
- Rotate credentials; set AWS_REGION; test with `aws s3 cp`

---

## 6) Frontend

### 6.1 CORS / Mixed content

Fix:
- Allow origin in API CORS
- Ensure HTTPS on both frontend and API

---

### 6.2 PDF download not working

Fix (blob):
```typescript
fetch('/api/irt/report/monthly/12', { headers })
  .then(res => res.blob())
  .then(blob => {
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = 'report.pdf'; a.click();
  });
```

---

### 6.3 Translations not loading

Fix:
- Ensure `irt` namespace added to i18n init
- Import shared translations from `shared/frontend/irt/locales`

---

## 7) Kubernetes

### 7.1 CronJob didn’t run

Checklist:
- Schedule uses cluster timezone
- LastScheduleTime / LastSuccessfulTime
- ConcurrencyPolicy; history limits

Inspect:
```bash
kubectl -n portal get cronjob irt-calibration-monthly -o yaml
kubectl -n portal get jobs --sort-by=.status.startTime
```

---

### 7.2 Ingress 404/502

Checklist:
- Service selector labels match
- TargetPort correct
- TLS secret present

---

## 8) SystemD

### 8.1 Service failed to start

Checklist:
- `EnvironmentFile=/etc/irt/irt.env` readable by service user
- Correct `WorkingDirectory` and `ExecStart`
- View logs

```bash
systemctl status irt-calibration.service
journalctl -u irt-calibration.service -b
```

---

### 8.2 Timer not firing

Inspect:
```bash
systemctl list-timers | grep irt
systemctl cat irt-calibration.timer
```

Fix:
- `OnCalendar=` syntax; `Persistent=true`

---

## 9) Monitoring & Logs

- API logs (K8s): `kubectl -n portal logs deploy/irt-api -f`
- Job logs (K8s): `kubectl -n portal logs job/<name>`
- SystemD: `journalctl -u irt-* -f`
- Sentry DSN set and environment labels

Alerting ideas:
- CronJob failure count > 0 in 24h
- Critical drift alerts > threshold
- API error rate > 1%

---

## 10) Known Errors & Fixes

| Error | Cause | Fix |
|------|-------|-----|
| `psycopg2.OperationalError: could not connect` | Wrong DB host/sg | Verify env, psql test |
| `relation ... does not exist` | Migration not run | `alembic upgrade head` |
| `Rhat > 1.01` | Poor MCMC convergence | Increase iter, adapt_delta |
| `divergent transitions` | Stan geometry | `adapt_delta=0.99`, reparam |
| `MemoryError` | Too many items/samples | Reduce draws/chains, batch |
| `CORS error` | Origin not allowed | Update CORS middleware |
| `SignatureDoesNotMatch` | S3 creds/region mismatch | Set region, rotate keys |
| `429 Too Many Requests` | Rate limit | Backoff, batch |

---

## 11) 한글 빠른 진단 (Korean Quick Guide)

### 1) 즉시 체크
- API 헬스: `/api/irt/health` → 200인가?
- DB 연결: API 컨테이너에서 `SELECT 1;` 실행 가능한가?
- 윈도우/알림 데이터 존재: `SELECT COUNT(*) FROM shared_irt.windows/drift_alerts`

### 2) 자주 발생하는 문제
- DB 연결 실패 → 환경변수/보안그룹/계정 확인, psql 테스트
- 마이그레이션 오류 → 권한/스키마/검색경로 확인 후 `alembic upgrade head`
- PyMC 메모리 → 샘플/체인 줄이기, 배치 처리, 메모리 상향
- brms 발산 → `adapt_delta=0.99`, `max_treedepth=15`, cmdstan 설치
- mirt 수렴불가 → 반복 증가, 2PL 사용, 응답 30개 미만 문항 제외
- PDF 오류/빈 문서 → pango/cairo/fonts 설치, base_url 설정, CJK 폰트
- S3 업로드 실패 → 자격증명/리전/버킷 정책 확인
- 프론트 CORS/404 → CORS 허용, 프록시/Ingress 경로 확인
- CronJob 미실행 → 스케줄/타임존/Job 로그 확인
- SystemD 타이머 미작동 → `list-timers`, `OnCalendar`, `Persistent=true`

### 3) 유용한 명령
```bash
# K8s 로그
kubectl -n portal logs deploy/irt-api -f
kubectl -n portal logs job/<name>

# SystemD 로그
journalctl -u irt-* -f

# DB 상태
psql "$DATABASE_URL" -c 'SELECT NOW(), CURRENT_SCHEMA;'
```

---

Author: DreamSeed AI Team
Last Updated: 2025-11-05
Related: 03_DRIFT_DETECTION_GUIDE.md, 04_API_INTEGRATION_GUIDE.md, 06_DEPLOYMENT_GUIDE.md
