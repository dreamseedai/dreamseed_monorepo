# r-irt-plumber Smoke Checks

r-irt-plumber 서비스와 IRT 캘리브레이션 CronJob을 검증하는 스모크 체크 가이드입니다.

## One-liner

모든 체크를 한 번에 실행 (health, service, pods, CronJob):

```bash
./apps/seedtest_api/scripts/smoke_check_irt.sh
```

## Manual Quick Checks

### Port-forward and Health Check (expects HTTP 200)

```bash
# 포트포워드 시작 (백그라운드)
kubectl -n seedtest port-forward deploy/r-irt-plumber 8001:8000 &

# Health check
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8001/healthz
# 예상 출력: 200

# 응답 본문 확인
curl -s http://127.0.0.1:8001/healthz
```

### CronJob Schedule

```bash
kubectl get cronjob -n seedtest calibrate-irt-nightly -o jsonpath='{.spec.schedule}'
# Expected: 0 3 * * *
```

### Recent Job Runs

```bash
# 최근 실행된 Job 목록
kubectl get jobs -n seedtest | grep calibrate-irt

# 특정 Job의 로그 확인
kubectl logs -n seedtest job/<calibrate-irt-nightly-xxxxxx>
```

## Optional Manual Run

CronJob을 수동으로 실행하여 테스트:

```bash
# 즉시 실행
kubectl create job --from=cronjob/calibrate-irt-nightly manual-calibrate-$(date +%s) -n seedtest

# 로그 확인 (실시간)
kubectl logs -n seedtest job/manual-calibrate-<timestamp> -f
```

## Where to Look

### Kubernetes Manifests

- **Deployment/Service/ServiceMonitor/NetworkPolicy/HPA**: 
  - `ops/k8s/r-irt-plumber/*`
  
- **Internal overlay** (no ingress):
  - `ops/k8s/r-irt-plumber/overlays/internal`

- **CronJob**:
  - `ops/k8s/cron/calibrate-irt.yaml`

- **Optional Argo CD app**:
  - `ops/argocd/apps/r-irt-plumber-internal.yaml`

### Documentation

- **Guide**: `apps/seedtest_api/docs/SMOKE_CHECKS.md` (이 파일)
- **Script**: `apps/seedtest_api/scripts/smoke_check_irt.sh`

## Troubleshooting

### Health Check 실패

```bash
# Pod 상태 확인
kubectl get pods -n seedtest -l app=r-irt-plumber

# Pod 로그 확인
kubectl logs -n seedtest -l app=r-irt-plumber --tail=50

# Pod 이벤트 확인
kubectl describe pod -n seedtest -l app=r-irt-plumber
```

### CronJob이 실행되지 않음

```bash
# CronJob 존재 확인
kubectl get cronjob -n seedtest calibrate-irt-nightly

# CronJob 상세 정보
kubectl describe cronjob -n seedtest calibrate-irt-nightly

# 수동 실행으로 테스트
kubectl create job --from=cronjob/calibrate-irt-nightly test-$(date +%s) -n seedtest
kubectl logs -n seedtest job/test-<timestamp> -f
```

## Expected Output

### Health Check 성공

```bash
$ curl -s http://127.0.0.1:8001/healthz
{"status":"ok","timestamp":"2025-01-15T10:30:00Z"}
# 또는
OK
```

### CronJob 로그 성공

```bash
$ kubectl logs -n seedtest job/calibrate-irt-nightly-1234567890
Running IRT calibration job...
Calibration upsert completed.
# 또는
No observations found; exiting.
```
