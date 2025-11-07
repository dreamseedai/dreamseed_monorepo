# 파이프라인 완전 배포 가이드 (3-5번 포함)

**작성일**: 2025-11-01

## 🎯 배포 목표

3-5번 항목을 완전히 활성화:
- 3) IRT 주간 캘리브레이션 라인 정합
- 4) θ 온라인 업데이트 (세션 종료 트리거)
- 5) 리포팅 (Quarto)

---

## 3) IRT 주간 캘리브레이션 활성화

### 현재 상태

- ✅ 코드: `apps/seedtest_api/jobs/mirt_calibrate.py` 완료
- ✅ CronJob: `calibrate-irt-weekly` 존재 (매주 일요일 03:10 UTC)
- ⚠️ r-irt-plumber 서비스: 배포 필요
- ⚠️ 이미지 경로: 수정 완료

### 배포 단계

#### Step 1: r-irt-plumber 서비스 배포

```bash
# Deployment 및 Service 배포
kubectl -n seedtest apply -f portal_front/ops/k8s/r-irt-plumber/deployment.yaml

# 배포 상태 확인
kubectl -n seedtest get deployment r-irt-plumber
kubectl -n seedtest get svc r-irt-plumber
kubectl -n seedtest get pods -l app=r-irt-plumber

# 서비스 헬스체크
kubectl -n seedtest exec -it $(kubectl -n seedtest get pods -l app=r-irt-plumber -o jsonpath='{.items[0].metadata.name}') -- curl -s http://localhost:8000/healthz || echo "Health check failed"
```

#### Step 2: CronJob 업데이트

```bash
# 이미지 경로 및 URL 수정된 CronJob 적용
kubectl -n seedtest apply -f portal_front/ops/k8s/cron/calibrate-irt.yaml

# 스케줄 확인 (현재: 매주 일요일 03:10 UTC)
kubectl -n seedtest get cronjob calibrate-irt-weekly -o jsonpath='{.spec.schedule}'

# 필요시 일일로 변경
kubectl -n seedtest patch cronjob calibrate-irt-weekly -p '{"spec":{"schedule":"0 3 * * *"}}'
```

#### Step 3: 수동 테스트

```bash
# Job 수동 생성 및 실행
kubectl -n seedtest create job --from=cronjob/calibrate-irt-weekly manual-irt-test-$(date +%s)

# 완료 대기
kubectl -n seedtest wait --for=condition=complete job/manual-irt-test-* --timeout=600s

# 로그 확인
kubectl -n seedtest logs job/manual-irt-test-* --tail=50
```

#### Step 4: 검증

```sql
-- IRT 파라미터 확인
SELECT item_id, model, params, fitted_at
FROM mirt_item_params
ORDER BY fitted_at DESC
LIMIT 10;

-- 능력 추정치 확인
SELECT user_id, theta, se, fitted_at
FROM mirt_ability
ORDER BY fitted_at DESC
LIMIT 10;
```

---

## 4) θ 온라인 업데이트 검증

### 현재 상태

- ✅ 코드 통합 완료: `finish_exam()`에 자동 트리거
- ✅ 서비스: `irt_update_service.py` 완료
- ⚠️ 검증 필요: 실제 세션으로 테스트

### 검증 단계

#### Step 1: 코드 통합 확인

```bash
# result_service.py에서 통합 확인
grep -A 10 "trigger_ability_update" apps/seedtest_api/services/result_service.py
```

#### Step 2: 실제 세션 테스트

```bash
# 1. 세션 생성 및 완료
# (FastAPI 엔드포인트를 통해 실제 세션 완료)

# 2. 로그 확인
kubectl -n seedtest logs -l app=seedtest-api | grep "trigger_ability_update" | tail -10

# 3. mirt_ability 업데이트 확인
psql $DATABASE_URL -c "SELECT user_id, theta, se, fitted_at FROM mirt_ability ORDER BY fitted_at DESC LIMIT 5;"
```

#### Step 3: (선택) 수동 트리거 엔드포인트 추가

필요시 FastAPI 엔드포인트 추가:

```python
@router.post("/analysis/irt/update")
async def trigger_irt_update(
    user_id: str,
    current_user: Any = Depends(get_current_user),
):
    from ..services.irt_update_service import trigger_ability_update
    trigger_ability_update(user_id, background=False)
    return {"status": "triggered", "user_id": user_id}
```

---

## 5) Quarto 리포팅 설정

### 현재 상태

- ✅ 코드: `generate_weekly_report.py` 완료
- ✅ 템플릿: `reports/quarto/weekly_report.qmd` 완료
- ✅ 마이그레이션: `20251101_1700_report_artifacts.py` 완료
- ⚠️ 런너 이미지: 빌드 필요
- ⚠️ S3 설정: Secret/ConfigMap 생성 필요

### 배포 단계

#### Step 1: Quarto 런너 이미지 빌드

```bash
# Dockerfile 확인
cat Dockerfile.quarto-runner

# 이미지 빌드
docker build -f Dockerfile.quarto-runner -t asia-northeast3-docker.pkg.dev/univprepai/seedtest/seedtest-report-runner:latest .

# 이미지 푸시
docker push asia-northeast3-docker.pkg.dev/univprepai/seedtest/seedtest-report-runner:latest

# 또는 GCR 사용 시
docker tag asia-northeast3-docker.pkg.dev/univprepai/seedtest/seedtest-report-runner:latest gcr.io/univprepai/seedtest-report-runner:latest
docker push gcr.io/univprepai/seedtest-report-runner:latest
```

#### Step 2: S3 Secret 및 ConfigMap 생성

```bash
# AWS S3 Secret 생성
kubectl -n seedtest create secret generic aws-s3-credentials \
  --from-literal=AWS_ACCESS_KEY_ID='<your-access-key>' \
  --from-literal=AWS_SECRET_ACCESS_KEY='<your-secret-key>'

# S3 버킷 ConfigMap 생성
kubectl -n seedtest create configmap report-config \
  --from-literal=S3_BUCKET=seedtest-reports \
  --from-literal=AWS_REGION=us-east-1
```

#### Step 3: 마이그레이션 적용

```bash
# report_artifacts 테이블 생성
cd apps/seedtest_api
export DATABASE_URL="postgresql://..."
alembic upgrade head

# 또는 K8s Pod에서 실행
kubectl -n seedtest exec -it <seedtest-api-pod> -- \
  bash -c "cd /app/apps/seedtest_api && alembic upgrade head"
```

#### Step 4: CronJob 배포

```bash
# generate-weekly-report.yaml 이미지 경로 확인 후 배포
kubectl -n seedtest apply -f portal_front/ops/k8s/cron/generate-weekly-report.yaml

# CronJob 확인
kubectl -n seedtest get cronjob generate-weekly-report
```

#### Step 5: 수동 테스트

```bash
# Job 수동 생성
kubectl -n seedtest create job --from=cronjob/generate-weekly-report manual-report-test-$(date +%s)

# 완료 대기
kubectl -n seedtest wait --for=condition=complete job/manual-report-test-* --timeout=1800s

# 로그 확인
kubectl -n seedtest logs job/manual-report-test-* --tail=100
```

#### Step 6: 검증

```sql
-- 리포트 아티팩트 확인
SELECT user_id, week_start, format, url, generated_at
FROM report_artifacts
ORDER BY generated_at DESC
LIMIT 10;
```

---

## 전체 배포 명령어 (한 번에 실행)

```bash
# 3번: IRT 캘리브레이션
kubectl -n seedtest apply -f portal_front/ops/k8s/r-irt-plumber/deployment.yaml
kubectl -n seedtest apply -f portal_front/ops/k8s/cron/calibrate-irt.yaml

# 4번: θ 온라인 업데이트 (코드 통합 완료, 추가 작업 없음)

# 5번: Quarto 리포팅 (이미지 빌드 및 S3 설정 후)
kubectl -n seedtest apply -f portal_front/ops/k8s/cron/generate-weekly-report.yaml
```

---

## 검증 체크리스트

### 3번 IRT 캘리브레이션

- [ ] r-irt-plumber Deployment 실행 중
- [ ] r-irt-plumber Service 접근 가능
- [ ] `calibrate-irt-weekly` CronJob 스케줄 확인
- [ ] 수동 실행 테스트 성공
- [ ] `mirt_item_params` 테이블에 데이터 입력 확인
- [ ] `mirt_ability` 테이블에 데이터 입력 확인

### 4번 θ 온라인 업데이트

- [ ] 세션 완료 시 로그에 `trigger_ability_update` 호출 확인
- [ ] `mirt_ability` 테이블에 최신 업데이트 확인
- [ ] 에러 없이 백그라운드 실행 확인

### 5번 Quarto 리포팅

- [ ] Quarto 런너 이미지 빌드 완료
- [ ] S3 Secret 및 ConfigMap 생성 완료
- [ ] `report_artifacts` 테이블 생성 확인
- [ ] 수동 실행 테스트 성공
- [ ] S3에 리포트 업로드 확인
- [ ] `report_artifacts` 테이블에 URL 저장 확인

---

## 문제 해결

### r-irt-plumber 서비스 연결 실패

```bash
# 서비스 상태 확인
kubectl -n seedtest get svc r-irt-plumber
kubectl -n seedtest get endpoints r-irt-plumber

# 파드 로그 확인
kubectl -n seedtest logs -l app=r-irt-plumber --tail=50

# 내부 네트워크 테스트
kubectl -n seedtest run test-curl --image=curlimages/curl --rm -it --restart=Never -- \
  curl -v http://r-irt-plumber.seedtest.svc.cluster.local:80/healthz
```

### Quarto 이미지 빌드 실패

```bash
# 로컬에서 테스트
docker run --rm -it asia-northeast3-docker.pkg.dev/univprepai/seedtest/seedtest-report-runner:latest \
  quarto --version

# Python 경로 테스트
docker run --rm -it asia-northeast3-docker.pkg.dev/univprepai/seedtest/seedtest-report-runner:latest \
  python3 -c "import sys; sys.path.insert(0, '/app'); from apps.seedtest_api.jobs import generate_weekly_report"
```

### S3 업로드 실패

```bash
# Secret 확인
kubectl -n seedtest get secret aws-s3-credentials -o jsonpath='{.data}' | base64 -d

# ConfigMap 확인
kubectl -n seedtest get configmap report-config -o yaml

# AWS 자격증명 테스트 (로컬)
aws s3 ls s3://<bucket-name>/reports/
```

---

## 참고 문서

- IRT 캘리브레이션: `apps/seedtest_api/docs/IRT_CALIBRATION_SETUP.md`
- θ 온라인 업데이트: `apps/seedtest_api/docs/THETA_ONLINE_UPDATE.md`
- Quarto 리포팅: `apps/seedtest_api/docs/QUARTO_REPORTING_GUIDE.md`
- 배포 체크리스트: `apps/seedtest_api/docs/DEPLOYMENT_CHECKLIST.md`

