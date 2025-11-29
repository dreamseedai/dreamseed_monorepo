# 🔄 프로덕션 자동 정리 전략

> **문제**: 수많은 유저가 데이터를 생성/삭제하면서 쓰레기 데이터가 산더미처럼 쌓임  
> **해법**: 무중단 자동 정리 시스템

---

## 📊 실제 프로덕션에서 쌓이는 쓰레기

### 1. 데이터베이스 쓰레기
```sql
-- 삭제된 학생의 오래된 학습 기록 (soft delete)
SELECT COUNT(*) FROM student_progress WHERE deleted_at IS NOT NULL AND deleted_at < NOW() - INTERVAL '90 days';
-- 예상: 수백만 건

-- 임시 세션 데이터 (만료됨)
SELECT COUNT(*) FROM user_sessions WHERE expires_at < NOW();
-- 예상: 수만 건/일

-- 중복 제출 데이터 (최신 것만 필요)
SELECT student_id, assignment_id, COUNT(*) FROM submissions 
GROUP BY student_id, assignment_id HAVING COUNT(*) > 1;
-- 예상: 수천 건
```

### 2. 파일 시스템 쓰레기
- 임시 업로드 파일: `/tmp/uploads/*` (수 GB/일)
- 오래된 로그: `/var/log/app/*.log` (수십 GB/주)
- 캐시 파일: `__pycache__`, `.next`, `node_modules/.cache` (수 GB)
- 오래된 백업: `/backup/*.sql` (수백 GB/월)

### 3. 메모리/캐시 쓰레기
- Redis 만료 안 된 세션: 수만 개
- Memcached 오래된 쿼리 캐시: 수 GB

---

## 🛡️ 무중단 자동 정리 시스템

### 전략 1: 데이터베이스 - VACUUM & PARTITION

#### PostgreSQL 자동 VACUUM
```sql
-- postgresql.conf 설정
autovacuum = on
autovacuum_vacuum_scale_factor = 0.1  -- 10% 변경 시 실행
autovacuum_analyze_scale_factor = 0.05
autovacuum_naptime = 1min
autovacuum_max_workers = 3

-- 수동 VACUUM (야간 시간대, 부하 낮을 때)
VACUUM ANALYZE student_progress;  -- 무중단, 읽기 가능
```

#### 파티션 기반 자동 삭제 (권장!)
```sql
-- 월별 파티션 생성 (PostgreSQL 10+)
CREATE TABLE student_progress (
    id BIGSERIAL,
    student_id INT,
    created_at TIMESTAMP NOT NULL,
    ...
) PARTITION BY RANGE (created_at);

-- 각 월별 파티션
CREATE TABLE student_progress_2024_11 PARTITION OF student_progress
    FOR VALUES FROM ('2024-11-01') TO ('2024-12-01');

CREATE TABLE student_progress_2024_12 PARTITION OF student_progress
    FOR VALUES FROM ('2024-12-01') TO ('2025-01-01');

-- 오래된 파티션 삭제 (0.001초, 무중단!)
DROP TABLE student_progress_2023_01;  -- 2년 전 데이터 즉시 삭제
```

**장점**:
- ✅ 수백만 건 DELETE 대신 **0.001초 DROP TABLE**
- ✅ 무중단 (다른 파티션은 계속 사용 가능)
- ✅ 자동화 가능

---

### 전략 2: 크론잡 자동 정리 (Kubernetes CronJob)

#### 데이터베이스 정리 크론잡
```yaml
# ops/k8s/cronjobs/db-cleanup.yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: db-cleanup-daily
spec:
  schedule: "0 2 * * *"  # 매일 오전 2시 (부하 최저)
  concurrencyPolicy: Forbid  # 중복 실행 방지
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: db-cleanup
            image: postgres:15
            env:
            - name: PGPASSWORD
              valueFrom:
                secretKeyRef:
                  name: db-credentials
                  key: password
            command:
            - /bin/sh
            - -c
            - |
              # 1. 90일 지난 soft delete 데이터 완전 삭제
              psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "
                DELETE FROM student_progress 
                WHERE deleted_at < NOW() - INTERVAL '90 days'
                LIMIT 10000;  -- 한 번에 10K씩만 삭제 (부하 분산)
              "
              
              # 2. 만료된 세션 삭제
              psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "
                DELETE FROM user_sessions 
                WHERE expires_at < NOW()
                LIMIT 5000;
              "
              
              # 3. VACUUM 실행
              psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "
                VACUUM ANALYZE student_progress;
              "
          restartPolicy: OnFailure
```

#### 파일 시스템 정리 크론잡
```yaml
# ops/k8s/cronjobs/fs-cleanup.yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: fs-cleanup-daily
spec:
  schedule: "0 3 * * *"  # 매일 오전 3시
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: fs-cleanup
            image: busybox
            volumeMounts:
            - name: app-logs
              mountPath: /var/log/app
            - name: temp-uploads
              mountPath: /tmp/uploads
            command:
            - /bin/sh
            - -c
            - |
              # 1. 7일 지난 로그 압축
              find /var/log/app -name "*.log" -mtime +7 -exec gzip {} \;
              
              # 2. 30일 지난 압축 로그 삭제
              find /var/log/app -name "*.log.gz" -mtime +30 -delete
              
              # 3. 1일 지난 임시 업로드 파일 삭제
              find /tmp/uploads -type f -mtime +1 -delete
              
              # 4. 빈 디렉토리 정리
              find /tmp/uploads -type d -empty -delete
              
              echo "정리 완료: $(date)"
          volumes:
          - name: app-logs
            persistentVolumeClaim:
              claimName: app-logs-pvc
          - name: temp-uploads
            persistentVolumeClaim:
              claimName: temp-uploads-pvc
          restartPolicy: OnFailure
```

---

### 전략 3: 애플리케이션 레벨 자동 정리

#### Python 백그라운드 작업 (Celery Beat)
```python
# backend/app/tasks/cleanup.py
from celery import Celery
from celery.schedules import crontab
from datetime import datetime, timedelta
import logging

app = Celery('cleanup')

@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    # 매일 오전 2시 실행
    sender.add_periodic_task(
        crontab(hour=2, minute=0),
        cleanup_old_data.s(),
        name='cleanup-old-data-daily'
    )
    
    # 매시간 실행
    sender.add_periodic_task(
        crontab(minute=0),
        cleanup_temp_files.s(),
        name='cleanup-temp-hourly'
    )

@app.task
def cleanup_old_data():
    """90일 지난 soft delete 데이터 정리 (배치 처리)"""
    logger = logging.getLogger(__name__)
    
    cutoff_date = datetime.now() - timedelta(days=90)
    batch_size = 10000
    total_deleted = 0
    
    while True:
        # 한 번에 10K씩만 삭제 (DB 부하 분산)
        deleted = db.session.execute(
            """
            DELETE FROM student_progress 
            WHERE id IN (
                SELECT id FROM student_progress 
                WHERE deleted_at < :cutoff 
                LIMIT :batch_size
            )
            """,
            {"cutoff": cutoff_date, "batch_size": batch_size}
        ).rowcount
        
        db.session.commit()
        total_deleted += deleted
        
        logger.info(f"Deleted {deleted} rows, total: {total_deleted}")
        
        if deleted < batch_size:
            break  # 더 이상 삭제할 것 없음
        
        # 다음 배치까지 1초 대기 (부하 분산)
        time.sleep(1)
    
    logger.info(f"Total deleted: {total_deleted} rows")
    return total_deleted

@app.task
def cleanup_temp_files():
    """1시간 지난 임시 파일 삭제"""
    import os
    import time
    
    temp_dir = "/tmp/uploads"
    cutoff_time = time.time() - 3600  # 1시간 전
    deleted_count = 0
    
    for filename in os.listdir(temp_dir):
        filepath = os.path.join(temp_dir, filename)
        
        if os.path.isfile(filepath):
            if os.path.getmtime(filepath) < cutoff_time:
                os.remove(filepath)
                deleted_count += 1
    
    return deleted_count
```

#### Celery Beat 스케줄러 실행
```yaml
# docker-compose.yml
services:
  celery-beat:
    build: ./backend
    command: celery -A app.tasks.cleanup beat --loglevel=info
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
      - DATABASE_URL=postgresql://...
    restart: always

  celery-worker:
    build: ./backend
    command: celery -A app.tasks.cleanup worker --loglevel=info --concurrency=2
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
      - DATABASE_URL=postgresql://...
    restart: always
```

---

### 전략 4: Redis/Memcached 자동 만료

#### Redis TTL 자동 설정
```python
# backend/app/cache.py
import redis
from datetime import timedelta

redis_client = redis.Redis(host='redis', port=6379, db=0)

# 세션: 24시간 후 자동 삭제
redis_client.setex(
    f"session:{user_id}",
    timedelta(hours=24),
    session_data
)

# 쿼리 캐시: 5분 후 자동 삭제
redis_client.setex(
    f"query:{query_hash}",
    timedelta(minutes=5),
    query_result
)

# 임시 데이터: 1시간 후 자동 삭제
redis_client.setex(
    f"temp:{temp_id}",
    timedelta(hours=1),
    temp_data
)
```

#### Redis 메모리 정책 설정
```conf
# redis.conf
maxmemory 2gb
maxmemory-policy allkeys-lru  # LRU로 자동 삭제

# 또는 volatile-lru (TTL 있는 것만 삭제)
maxmemory-policy volatile-lru
```

---

### 전략 5: S3/Object Storage 생명주기 정책

#### AWS S3 Lifecycle Policy
```json
{
  "Rules": [
    {
      "Id": "delete-temp-uploads-after-7-days",
      "Status": "Enabled",
      "Prefix": "temp-uploads/",
      "Expiration": {
        "Days": 7
      }
    },
    {
      "Id": "archive-old-logs-to-glacier",
      "Status": "Enabled",
      "Prefix": "logs/",
      "Transitions": [
        {
          "Days": 30,
          "StorageClass": "GLACIER"
        }
      ],
      "Expiration": {
        "Days": 365
      }
    },
    {
      "Id": "delete-old-backups",
      "Status": "Enabled",
      "Prefix": "backups/",
      "Expiration": {
        "Days": 90
      }
    }
  ]
}
```

**적용**:
```bash
aws s3api put-bucket-lifecycle-configuration \
  --bucket dreamseed-storage \
  --lifecycle-configuration file://lifecycle-policy.json
```

---

## 🚀 추천 통합 전략

### 1단계: 즉시 적용 (1주일)
```bash
# 1. PostgreSQL 파티셔닝 설정
# - student_progress, submissions, logs 테이블

# 2. Kubernetes CronJob 배포
kubectl apply -f ops/k8s/cronjobs/db-cleanup.yaml
kubectl apply -f ops/k8s/cronjobs/fs-cleanup.yaml

# 3. Redis TTL 적용
# - 모든 캐시에 적절한 만료 시간 설정
```

### 2단계: 자동화 강화 (1개월)
```bash
# 1. Celery Beat 배포
docker-compose up -d celery-beat celery-worker

# 2. S3 Lifecycle Policy 적용
aws s3api put-bucket-lifecycle-configuration ...

# 3. 모니터링 대시보드 구축 (Grafana)
# - 데이터 증가율 모니터링
# - 정리 작업 성공/실패 알림
```

### 3단계: 최적화 (3개월)
```bash
# 1. 데이터 아카이빙 자동화
# - 1년 지난 데이터 → S3 Glacier

# 2. 정리 작업 성능 튜닝
# - 배치 크기 최적화
# - 실행 시간대 조정

# 3. 자동 복구 시스템
# - 정리 실패 시 재시도
# - 슬랙/이메일 알림
```

---

## 📊 예상 효과

### Before (자동 정리 없음)
- ❌ DB 크기: 월 100GB 증가
- ❌ 디스크 사용량: 월 500GB 증가
- ❌ 쿼리 속도: 점점 느려짐
- ❌ 수동 정리 필요: 주 1회, 4시간

### After (자동 정리 시스템)
- ✅ DB 크기: 월 10GB 증가 (90% 감소)
- ✅ 디스크 사용량: 월 50GB 증가 (90% 감소)
- ✅ 쿼리 속도: 항상 빠름
- ✅ 수동 개입: 불필요

### ROI (투자 대비 효과)
| 항목 | 비용 | 절감 효과 |
|-----|------|----------|
| DB 스토리지 | -$10/월 | +$90/월 (90% 감소) |
| S3 스토리지 | -$5/월 | +$45/월 (90% 감소) |
| 운영 인력 | -$500/월 (개발) | +$2,000/월 (수동 정리 불필요) |
| **총합** | **-$515/월** | **+$2,135/월** |

**순이익: $1,620/월**

---

## 🔧 모니터링 & 알림

### Grafana 대시보드
```yaml
# ops/monitoring/grafana/dashboards/cleanup-monitoring.json
{
  "panels": [
    {
      "title": "DB 크기 추이",
      "targets": [{
        "expr": "pg_database_size_bytes{database=\"dreamseed\"}"
      }]
    },
    {
      "title": "정리 작업 성공률",
      "targets": [{
        "expr": "rate(cleanup_job_success_total[1h])"
      }]
    },
    {
      "title": "디스크 사용량",
      "targets": [{
        "expr": "node_filesystem_avail_bytes"
      }]
    }
  ]
}
```

### Slack 알림
```python
# backend/app/tasks/cleanup.py
import requests

def send_slack_alert(message):
    webhook_url = os.getenv("SLACK_WEBHOOK_URL")
    requests.post(webhook_url, json={"text": message})

@app.task
def cleanup_old_data():
    try:
        deleted = ...  # 정리 작업
        send_slack_alert(f"✅ 정리 완료: {deleted}건 삭제")
    except Exception as e:
        send_slack_alert(f"❌ 정리 실패: {str(e)}")
        raise
```

---

## 🎯 핵심 원칙

1. **자동화**: 사람이 개입하지 않아도 24/7 자동 실행
2. **무중단**: 서비스 중단 없이 백그라운드 실행
3. **점진적**: 한 번에 대량 삭제 대신 배치 처리
4. **모니터링**: 실시간 알림 & 대시보드
5. **안전성**: 백업 → 정리 → 검증 순서

---

## 📚 참고 자료

- [PostgreSQL Partitioning](https://www.postgresql.org/docs/current/ddl-partitioning.html)
- [Kubernetes CronJobs](https://kubernetes.io/docs/concepts/workloads/controllers/cron-jobs/)
- [Celery Beat](https://docs.celeryq.dev/en/stable/userguide/periodic-tasks.html)
- [AWS S3 Lifecycle](https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lifecycle-mgmt.html)
- [Redis Memory Management](https://redis.io/docs/manual/eviction/)

---

**결론**: 프로덕션 환경에서는 **자동 정리 시스템이 필수**입니다. 
한 번 구축하면 수년간 무중단으로 작동하며, 운영 비용을 90% 절감할 수 있습니다.
