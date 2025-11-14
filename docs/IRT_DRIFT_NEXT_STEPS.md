# IRT 드리프트 시스템 - 다음 작업 가이드

**작성일**: 2025-11-07  
**현재 상태**: 기반 인프라 완성, API 서버 실행 중

---

## 📋 오늘 완료된 작업 (2025-11-07)

### ✅ 완료 항목
1. **DB 스키마 생성** - PostgreSQL 테이블 4개
2. **R 코드 배치** - 파이프라인 + API 코드
3. **시스템 의존성** - libpq-dev, libsodium-dev
4. **R 패키지 설치** - DBI, RPostgres, dplyr, tidyr, mirt, rstan, plumber
5. **API 서버 실행** - 포트 9999에서 실행 중
6. **샘플 기준 파라미터** - 5개 문항
7. **샘플 응답 데이터** - 5,000개 (최근 8주, 501개 문항, 3명 사용자)

---

## 🚀 내일 시작하는 방법

### Step 1: API 서버 재시작

```bash
# 1. 작업 디렉토리로 이동
cd /home/won/projects/dreamseed_monorepo/portal_front/r-irt-plumber

# 2. 환경 변수 설정 및 서버 시작
PGHOST=127.0.0.1 \
PGPORT=5432 \
PGUSER=postgres \
PGPASSWORD="DreamSeedAi@0908" \
PGDATABASE=dreamseed \
Rscript -e ".libPaths(Sys.getenv('R_LIBS_USER')); library(plumber); pr <- plumb('plumber_drift.R'); pr\$run(host='0.0.0.0', port=9999)"
```

**또는 백그라운드 실행**:
```bash
nohup Rscript -e ".libPaths(Sys.getenv('R_LIBS_USER')); library(plumber); pr <- plumb('plumber_drift.R'); pr\$run(host='0.0.0.0', port=9999)" > /tmp/irt_api.log 2>&1 &
```

### Step 2: 서버 상태 확인

```bash
# 헬스 체크
curl http://localhost:9999/health

# 설정 확인
curl http://localhost:9999/config

# Swagger UI 열기
# 브라우저에서: http://localhost:9999/__docs__/
```

---

## 📝 다음 작업 목록

### Phase 1: FastAPI 통합 (1-2시간)

#### 1. FastAPI 라우터 생성
```bash
# 파일 생성
touch /home/won/projects/dreamseed_monorepo/apps/seedtest_api/routers/irt_drift.py
```

**내용**: `/docs/IRT_DRIFT_CONTROL_GUIDE.md` 섹션 5 코드 복사

#### 2. 라우터 등록
```python
# /apps/seedtest_api/main.py 수정
from apps.seedtest_api.routers import irt_drift

app.include_router(irt_drift.router)
```

#### 3. 환경 변수 설정
```bash
# .env 또는 환경 변수
export R_IRT_BASE_URL=http://localhost:9999
export R_IRT_TIMEOUT=3600.0
```

#### 4. 테스트
```bash
# FastAPI 서버 재시작
# 테스트
curl http://localhost:8080/api/irt/drift/stats?since_days=30
```

---

### Phase 2: Celery 배치 작업 (1시간)

#### 1. Celery 작업 생성
```bash
# 파일 생성
touch /home/won/projects/dreamseed_monorepo/shared/tasks/irt_drift.py
```

**내용**: `/docs/IRT_DRIFT_CONTROL_GUIDE.md` 섹션 7 코드 복사

#### 2. Celery Beat 스케줄 등록
```python
# /shared/celery_config.py 수정
from celery.schedules import crontab

beat_schedule = {
    "weekly-irt-drift": {
        "task": "irt.weekly_drift_detection",
        "schedule": crontab(day_of_week=0, hour=3, minute=0),
    },
}
```

#### 3. 환경 변수
```bash
export SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

#### 4. 수동 테스트
```bash
# Celery 워커 시작
celery -A shared.celery_app worker --loglevel=info

# 작업 실행 (다른 터미널)
python -c "from shared.tasks.irt_drift import weekly_drift_detection; weekly_drift_detection.delay()"
```

---

### Phase 3: 교사 대시보드 UI (2-3시간)

#### 1. 대시보드 코드 추가
```bash
# 파일 수정
nano /home/won/projects/dreamseed_monorepo/portal_front/dashboard/app_teacher.R
```

**내용**: `/docs/IRT_DRIFT_CONTROL_GUIDE.md` 섹션 6 코드 추가

#### 2. 환경 변수
```bash
export R_IRT_BASE_URL=http://localhost:9999
```

#### 3. 대시보드 실행
```bash
cd /home/won/projects/dreamseed_monorepo/portal_front/dashboard
Rscript -e 'shiny::runApp("app_teacher.R", host="0.0.0.0", port=8081)'
```

---

## 🔍 문제 해결

### 문제 1: R 패키지 로드 실패
```bash
# R 라이브러리 경로 확인
Rscript -e ".libPaths()"

# 패키지 재설치
Rscript -e ".libPaths(Sys.getenv('R_LIBS_USER')); install.packages('패키지명', repos='https://cloud.r-project.org')"
```

### 문제 2: PostgreSQL 연결 실패
```bash
# 연결 테스트
PGPASSWORD="DreamSeedAi@0908" psql -h 127.0.0.1 -p 5432 -U postgres -d dreamseed -c "SELECT version();"

# 환경 변수 확인
echo $PGHOST $PGPORT $PGUSER $PGDATABASE
```

### 문제 3: 포트 충돌
```bash
# 사용 중인 포트 확인
netstat -tuln | grep 9999

# 프로세스 종료
pkill -f "plumber_drift.R"
```

---

## 📚 참고 문서

### 주요 문서
1. **완전 구현 가이드**: `/docs/IRT_DRIFT_CONTROL_GUIDE.md`
2. **배포 체크리스트**: `/docs/IRT_DRIFT_IMPLEMENTATION_SUMMARY.md`
3. **다음 작업 가이드**: 이 문서

### 코드 위치
- **R 파이프라인**: `/portal_front/r-irt-plumber/irt_drift_pipeline.R`
- **Plumber API**: `/portal_front/r-irt-plumber/plumber_drift.R`
- **FastAPI 라우터**: (생성 예정) `/apps/seedtest_api/routers/irt_drift.py`
- **Celery 작업**: (생성 예정) `/shared/tasks/irt_drift.py`

---

## ⚡ 빠른 시작 스크립트

### 전체 환경 재시작
```bash
#!/bin/bash
# restart_irt_drift.sh

echo "🚀 IRT 드리프트 시스템 재시작..."

# 1. R API 서버 시작
cd /home/won/projects/dreamseed_monorepo/portal_front/r-irt-plumber
PGHOST=127.0.0.1 \
PGPORT=5432 \
PGUSER=postgres \
PGPASSWORD="DreamSeedAi@0908" \
PGDATABASE=dreamseed \
nohup Rscript -e ".libPaths(Sys.getenv('R_LIBS_USER')); library(plumber); pr <- plumb('plumber_drift.R'); pr\$run(host='0.0.0.0', port=9999)" > /tmp/irt_api.log 2>&1 &

echo "⏳ API 서버 시작 대기 (5초)..."
sleep 5

# 2. 헬스 체크
echo "🔍 헬스 체크..."
curl -s http://localhost:9999/health | jq .

echo "✅ 시스템 준비 완료!"
echo "📊 Swagger UI: http://localhost:9999/__docs__/"
```

**사용법**:
```bash
chmod +x restart_irt_drift.sh
./restart_irt_drift.sh
```

---

## 📊 현재 데이터 상태

### DB 테이블
```sql
-- 확인 쿼리
SELECT 'baseline' AS table_name, COUNT(*) FROM irt_item_params_baseline
UNION ALL
SELECT 'latest', COUNT(*) FROM irt_item_params_latest
UNION ALL
SELECT 'drift_log', COUNT(*) FROM item_drift_log
UNION ALL
SELECT 'responses', COUNT(*) FROM view_item_responses_recent;
```

**실제 결과** (2025-11-07 완료):
```
table_name  | count
------------|------
baseline    |     5  ✅
latest      |     0
drift_log   |     0
responses   |  4954  ✅ (최근 8주 응답 데이터)
content     |   501  ✅ (문항 데이터)
attempts    |  5000  ✅ (전체 응답 데이터)
```

**응답 데이터 상세**:
- 전체 응답: 5,000개
- 최근 8주: 4,954개
- 고유 문항: 501개
- 고유 사용자: 3명
- 정답률: 72.0%
- 평균 점수: 65.0점
- 문항당 평균 응답: 9.9개

---

## 🎯 우선순위

### 높음 (내일 필수)
1. ✅ FastAPI 통합 - Python 백엔드 연동
2. ✅ 기본 테스트 - 엔드포인트 검증

### 중간 (이번 주)
3. ⏳ Celery 배치 작업 - 주간 자동 실행
4. ⏳ 교사 대시보드 UI - 모니터링 화면

### 낮음 (다음 주)
5. ⏳ Docker 이미지 빌드
6. ⏳ Kubernetes 배포
7. ⏳ 프로덕션 데이터 마이그레이션

---

## 🔄 샘플 데이터 재생성 (필요 시)

### 응답 데이터 삭제 및 재생성
```bash
PGPASSWORD="DreamSeedAi@0908" psql -h 127.0.0.1 -p 5432 -U postgres -d dreamseed << 'EOF'
-- 기존 데이터 삭제
TRUNCATE attempts CASCADE;
TRUNCATE content CASCADE;

-- content 테이블에 문항 추가
INSERT INTO content (id, title, doc, author_id, created_at, updated_at)
SELECT 
    id,
    LEFT(normalized_title, 250),
    jsonb_build_object('question', content_question_mj, 'difficulty', difficulty_level, 'subject', subject),
    1,
    NOW() - (RANDOM() * 90 || ' days')::INTERVAL,
    NOW()
FROM ds_questions
WHERE id IN (SELECT id FROM ds_questions ORDER BY RANDOM() LIMIT 500)
ON CONFLICT (id) DO NOTHING;

-- 응답 데이터 생성 (5000개)
DO $$
DECLARE
    v_user_id INT;
    v_content_id INT;
    v_score INT;
    v_days_ago INT;
    i INT;
    content_ids INT[];
BEGIN
    SELECT ARRAY_AGG(id) INTO content_ids FROM content;
    FOR i IN 1..5000 LOOP
        v_user_id := (RANDOM() * 2 + 1)::INT;
        v_content_id := content_ids[(RANDOM() * (array_length(content_ids, 1) - 1) + 1)::INT];
        v_score := CASE WHEN RANDOM() < 0.6 THEN (RANDOM() * 30 + 70)::INT ELSE (RANDOM() * 70)::INT END;
        v_days_ago := (RANDOM() * 56)::INT;
        INSERT INTO attempts (user_id, content_id, score, created_at, org_id)
        VALUES (v_user_id, v_content_id, v_score, NOW() - (v_days_ago || ' days')::INTERVAL, 1);
    END LOOP;
END $$;

SELECT '✅ 샘플 데이터 재생성 완료' AS status, COUNT(*) AS count FROM attempts;
EOF
```

### 더 많은 응답 데이터 생성 (50,000개)
```bash
# 위 스크립트에서 5000을 50000으로 변경
# 문항당 평균 100개 응답 (IRT 추정에 적합)
```

---

## 💡 팁

### R 세션 유지
```bash
# tmux 사용 (추천)
tmux new -s irt-api
# 서버 시작 후 Ctrl+B, D로 detach
# 재접속: tmux attach -t irt-api
```

### 로그 모니터링
```bash
# API 로그
tail -f /tmp/irt_api.log

# PostgreSQL 로그
sudo tail -f /var/log/postgresql/postgresql-16-main.log
```

### 성능 모니터링
```bash
# R 프로세스 확인
ps aux | grep Rscript

# 메모리 사용량
free -h

# 디스크 사용량
df -h
```

---

**내일 시작 시 이 문서를 참고하세요!** 📖
