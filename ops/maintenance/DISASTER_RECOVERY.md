# 🔥 재해 복구 계획 (Disaster Recovery Plan)

> **"모든 것은 언젠가 망가진다. 준비된 자만 살아남는다."**  
> **작성일**: 2025년 11월 11일  
> **목표**: RPO 15분, RTO 1시간 달성

---

## 📌 Executive Summary

### DR 목표 (RTO/RPO)

```yaml
Phase 1-2 (MVP/베타):
  RPO (Recovery Point Objective): 1시간
  RTO (Recovery Time Objective): 4시간
  가용성 목표: 99.0%
  
Phase 3-4 (런칭/성장):
  RPO: 15분
  RTO: 1시간
  가용성 목표: 99.5%
  
Phase 5 (대규모):
  RPO: 5분
  RTO: 30분
  가용성 목표: 99.9%
```

### 장애 분류

```yaml
P0 (Critical): 서비스 완전 다운
  - 예상 복구 시간: < 1시간
  - 온콜: 즉시 호출
  - 예: DB 장애, 전체 서버 다운
  
P1 (High): 주요 기능 장애
  - 예상 복구 시간: < 4시간
  - 온콜: 30분 내 응답
  - 예: AI 피드백 불가, 로그인 느림
  
P2 (Medium): 부분 기능 장애
  - 예상 복구 시간: < 24시간
  - 온콜: 업무시간 내 처리
  - 예: 통계 대시보드 오류
  
P3 (Low): 경미한 불편
  - 예상 복구 시간: < 1주
  - 온콜: 불필요
  - 예: UI 버그, 오타
```

---

## 💥 A) 장애 시나리오 & 대응

### Scenario 1: PostgreSQL Primary 장애 🔴

**증상**:
- API 500 에러 급증
- `/health` 엔드포인트 실패
- Grafana DB 연결 끊김 알람

**원인 가능성**:
- 디스크 꽉 참 (90%+)
- 프로세스 크래시
- 하드웨어 고장
- 데이터 손상

**즉시 조치** (0~5분):

```bash
#!/bin/bash
# db_emergency_response.sh

echo "🚨 PostgreSQL 장애 대응 시작"

# 1. 상태 확인
echo "Step 1: DB 상태 확인..."
systemctl status postgresql
pg_isready -h localhost -p 5432

# 2. Read Replica로 읽기 트래픽 전환
echo "Step 2: Read Replica로 전환..."
# API 서버 환경 변수 업데이트
export DATABASE_READ_URL="postgresql://replica1:5432/dreamseed"

# API 서버 재시작 (읽기만 가능)
docker restart api-server

# 3. 사용자에게 알림
echo "Step 3: 사용자 알림..."
# 상태 페이지 업데이트
curl -X POST https://status.dreamseed.ai/incidents \
  -d "status=investigating" \
  -d "message=데이터베이스 장애 조사 중입니다."

echo "✅ 긴급 조치 완료 (읽기 전용 모드)"
```

**복구 절차** (5분~1시간):

```bash
#!/bin/bash
# db_recovery.sh

echo "🔧 PostgreSQL 복구 시작"

# 1. 디스크 공간 확인
df -h /var/lib/postgresql

# 2. 로그 확인
tail -100 /var/log/postgresql/postgresql.log

# 3. 복구 시도
case "$FAILURE_TYPE" in
  "disk_full")
    # 오래된 WAL 삭제
    find /var/lib/postgresql/15/main/pg_wal -mtime +7 -delete
    ;;
  
  "crash")
    # PostgreSQL 재시작
    systemctl restart postgresql
    ;;
  
  "corruption")
    # 백업에서 복구
    pg_restore -d dreamseed /backup/latest.dump
    ;;
esac

# 4. 복구 검증
psql -c "SELECT 1" dreamseed

# 5. Primary로 다시 전환
export DATABASE_URL="postgresql://localhost:5432/dreamseed"
docker restart api-server

echo "✅ PostgreSQL 복구 완료"
```

**페일오버 (최악의 경우)**:

```bash
#!/bin/bash
# db_failover_to_cloud.sh
# 로컬 DB 복구 불가 시 Cloud SQL로 전환

echo "☁️ Cloud SQL DR로 Failover..."

# 1. Cloud SQL 인스턴스 시작
gcloud sql instances patch dreamseed-dr \
  --activation-policy=ALWAYS

# 2. 최신 백업 복구
gcloud sql backups restore BACKUP_ID \
  --backup-instance=dreamseed-dr

# 3. 애플리케이션 연결 전환
export DATABASE_URL="postgresql://CLOUD_SQL_IP:5432/dreamseed"
kubectl set env deployment/api-server DATABASE_URL=$DATABASE_URL

# 4. DNS 업데이트 (선택)
# db.dreamseed.ai → Cloud SQL IP

echo "✅ Cloud SQL로 전환 완료"
echo "⚠️ 로컬 DB 복구 후 다시 전환 필요"
```

**예상 복구 시간**:
- 재시작으로 해결: **5분**
- 백업 복구: **30분**
- Cloud SQL Failover: **1시간**

---

### Scenario 2: GPU 하드웨어 고장 🔥

**증상**:
- `nvidia-smi` 응답 없음
- vLLM 서버 크래시
- AI 피드백 요청 실패

**원인**:
- GPU 과열 (>90°C)
- 전원 공급 문제
- 드라이버 충돌
- 하드웨어 물리적 고장

**즉시 조치**:

```bash
#!/bin/bash
# gpu_emergency.sh

echo "🔥 GPU 장애 대응"

# 1. GPU 상태 확인
nvidia-smi || echo "❌ nvidia-smi 실패"

# 2. vLLM 서버 중단
docker stop vllm-server

# 3. GPU 리셋 시도
sudo nvidia-smi --gpu-reset

# 4. 드라이버 재로드
sudo rmmod nvidia_uvm
sudo rmmod nvidia
sudo modprobe nvidia

# 5. 재시작 시도
nvidia-smi

if [ $? -eq 0 ]; then
    echo "✅ GPU 복구 성공"
    docker start vllm-server
else
    echo "❌ GPU 복구 실패 - Spot GPU로 Failover"
    ./start_spot_gpu.sh
fi
```

**Spot GPU Failover**:

```bash
#!/bin/bash
# start_spot_gpu.sh

echo "☁️ GCP Spot GPU로 긴급 전환"

# 1. Spot GPU 인스턴스 생성
gcloud compute instances create gpu-emergency-$(date +%s) \
  --zone=us-central1-a \
  --machine-type=n1-standard-8 \
  --accelerator=type=nvidia-tesla-t4,count=1 \
  --preemptible \
  --image-family=pytorch-latest-gpu \
  --image-project=deeplearning-platform-release \
  --boot-disk-size=100GB \
  --metadata=startup-script='#!/bin/bash
    # vLLM 서버 자동 설치 및 시작
    docker run -d -p 8000:8000 vllm/vllm-openai \
      --model meta-llama/Llama-2-13b-chat-hf
  '

# 2. API 서버에 새 GPU 엔드포인트 설정
export GPU_ENDPOINT="http://SPOT_GPU_IP:8000"
kubectl set env deployment/api-server GPU_ENDPOINT=$GPU_ENDPOINT

echo "✅ Spot GPU Failover 완료"
echo "⚠️ 비용: $0.35/시간"
echo "⚠️ 로컬 GPU 수리 후 다시 전환 필요"
```

**예상 복구 시간**:
- GPU 리셋: **5분**
- Spot GPU Failover: **15분**
- 하드웨어 교체: **2~24시간**

---

### Scenario 3: 전체 서버 다운 (정전/화재) ⚡

**증상**:
- 모든 서비스 응답 없음
- 네트워크 연결 끊김
- 헬스체크 실패

**복구 절차** (Full DR):

```bash
#!/bin/bash
# full_disaster_recovery.sh
# 전체 재해 시 클라우드로 완전 전환

echo "🚨 전체 재해 복구 시작"

# 1. Cloud SQL 활성화
gcloud sql instances patch dreamseed-dr \
  --activation-policy=ALWAYS

# 2. 최신 백업 복구 (Backblaze B2에서)
b2 download-file dreamseed-backups postgres/latest.sql.gz /tmp/
gunzip /tmp/latest.sql.gz
gcloud sql import sql dreamseed-dr /tmp/latest.sql

# 3. Cloud Run API 서버 최대 확장
gcloud run services update dreamseed-api \
  --min-instances=10 \
  --max-instances=40

# 4. GCP GPU 인스턴스 대량 생성
for i in {1..5}; do
  gcloud compute instances create gpu-dr-$i \
    --zone=us-central1-a \
    --machine-type=n1-standard-8 \
    --accelerator=type=nvidia-tesla-t4,count=1
done

# 5. DNS 완전 전환
# db.dreamseed.ai → Cloud SQL
# gpu.dreamseed.ai → GCP GPU 로드 밸런서

# 6. 상태 페이지 업데이트
curl -X POST https://status.dreamseed.ai/incidents \
  -d "status=monitoring" \
  -d "message=클라우드 DR로 전환 완료. 서비스 재개."

echo "✅ Full DR 완료"
echo "💰 예상 비용: $500/일"
```

**예상 복구 시간**: **2~4시간**

---

### Scenario 4: 네트워크 단절 (ISP 장애) 🌐

**증상**:
- 외부에서 서비스 접근 불가
- 내부 시스템은 정상

**복구**:

```bash
#!/bin/bash
# network_failover.sh

# 1. Cloudflare 상태 페이지 표시
# "일시적 네트워크 장애. 복구 중..."

# 2. 대체 ISP로 전환 (준비된 경우)
# 또는

# 3. 임시로 Cloud Run만 운영
# (로컬 GPU 없이 OpenAI API 사용)
export OPENAI_API_KEY="sk-..."
export USE_OPENAI_FALLBACK=true
kubectl set env deployment/api-server USE_OPENAI_FALLBACK=true

echo "✅ OpenAI Fallback 모드로 전환"
echo "⚠️ 비용 증가 예상"
```

---

### Scenario 5: DDoS 공격 🛡️

**증상**:
- 트래픽 급증 (1000배)
- 정상 사용자 접근 불가
- 서버 과부하

**대응**:

```bash
#!/bin/bash
# ddos_mitigation.sh

echo "🛡️ DDoS 방어 활성화"

# 1. Cloudflare "Under Attack" 모드
curl -X PATCH "https://api.cloudflare.com/client/v4/zones/ZONE_ID/settings/security_level" \
  -H "Authorization: Bearer TOKEN" \
  -d '{"value":"under_attack"}'

# 2. Rate Limiting 강화 (긴급)
# API: 10/min → 5/min
# IP: 1000/hour → 100/hour

# 3. IP 차단 (악의적 IP 식별 후)
iptables -A INPUT -s MALICIOUS_IP -j DROP

# 4. Cloud Run 최대 인스턴스 제한 (비용 보호)
gcloud run services update dreamseed-api \
  --max-instances=20  # 무제한 스케일링 방지

echo "✅ DDoS 방어 활성화"
```

---

### Scenario 6: 데이터 손상/삭제 (악의적/실수) 💀

**증상**:
- 데이터 일부 또는 전체 삭제
- 테이블 드롭
- SQL Injection 공격

**복구**:

```bash
#!/bin/bash
# data_recovery.sh

echo "💾 데이터 복구 시작"

# 1. 즉시 DB 읽기 전용 모드
psql -c "ALTER DATABASE dreamseed SET default_transaction_read_only = on;"

# 2. 삭제된 데이터 확인
psql -c "SELECT * FROM pg_stat_activity WHERE state = 'DELETE';"

# 3. 최근 백업에서 복구
BACKUP_TIME="2025-11-11 14:00:00"
pg_restore -d dreamseed_temp /backup/backup_$(date -d "$BACKUP_TIME" +%Y%m%d).dump

# 4. 삭제된 데이터만 복구 (diff)
# (수동 작업 필요)

# 5. 보안 점검
# SQL Injection 취약점 패치
# 악의적 사용자 계정 비활성화

echo "✅ 데이터 복구 완료"
```

---

## 🔧 B) 백업 전략

### 1️⃣ PostgreSQL 백업

**일일 풀 백업** (새벽 3시):

```bash
#!/bin/bash
# daily_backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backup"
B2_BUCKET="dreamseed-backups"

# 1. PostgreSQL 풀 덤프
pg_dump -U postgres dreamseed | gzip > $BACKUP_DIR/postgres_$DATE.sql.gz

# 2. Backblaze B2 업로드
b2 upload-file $B2_BUCKET $BACKUP_DIR/postgres_$DATE.sql.gz postgres/daily/$DATE.sql.gz

# 3. 로컬 백업 7일치만 유지
find $BACKUP_DIR -name "postgres_*.sql.gz" -mtime +7 -delete

# 4. B2 백업 30일치만 유지
b2 ls $B2_BUCKET postgres/daily/ | \
  awk -v cutoff=$(date -d '30 days ago' +%Y%m%d) '$1 < cutoff {print $2}' | \
  xargs -I {} b2 delete-file-version $B2_BUCKET {}

echo "✅ 일일 백업 완료: $DATE"
```

**15분 WAL 아카이빙** (RPO 15분):

```bash
#!/bin/bash
# wal_archive.sh
# PostgreSQL 설정에서 호출됨

WAL_FILE=$1
WAL_PATH="/var/lib/postgresql/15/main/pg_wal/$WAL_FILE"
B2_BUCKET="dreamseed-backups"

# Backblaze B2로 WAL 전송
b2 upload-file $B2_BUCKET $WAL_PATH postgres/wal/$WAL_FILE

# 성공 시 로컬 WAL 삭제
if [ $? -eq 0 ]; then
    rm $WAL_PATH
fi
```

**PostgreSQL 설정** (`postgresql.conf`):

```conf
# WAL 아카이빙 활성화
wal_level = replica
archive_mode = on
archive_command = '/scripts/wal_archive.sh %f'

# WAL 보관 (최소 16개 파일)
wal_keep_size = 1GB

# 백업용 슬롯
max_wal_senders = 3
```

### 2️⃣ 애플리케이션 데이터 백업

```bash
#!/bin/bash
# app_backup.sh

DATE=$(date +%Y%m%d_%H%M%S)

# 1. 모델 파일 백업 (주 1회)
tar -czf /backup/models_$DATE.tar.gz /models

# 2. 사용자 업로드 파일
tar -czf /backup/uploads_$DATE.tar.gz /uploads

# 3. 설정 파일
tar -czf /backup/configs_$DATE.tar.gz /etc/dreamseed

# 4. B2 업로드
b2 upload-file dreamseed-backups /backup/models_$DATE.tar.gz app/models/$DATE.tar.gz
b2 upload-file dreamseed-backups /backup/uploads_$DATE.tar.gz app/uploads/$DATE.tar.gz
b2 upload-file dreamseed-backups /backup/configs_$DATE.tar.gz app/configs/$DATE.tar.gz
```

### 3️⃣ 백업 복구 테스트 (월 1회)

```bash
#!/bin/bash
# backup_restore_test.sh
# 매월 1일 자동 실행

echo "🧪 백업 복구 테스트 시작"

# 1. 최신 백업 다운로드
LATEST_BACKUP=$(b2 ls dreamseed-backups postgres/daily/ | tail -1)
b2 download-file dreamseed-backups $LATEST_BACKUP /tmp/test_backup.sql.gz

# 2. 테스트 DB에 복구
gunzip /tmp/test_backup.sql.gz
psql -U postgres -c "DROP DATABASE IF EXISTS dreamseed_test;"
psql -U postgres -c "CREATE DATABASE dreamseed_test;"
psql -U postgres dreamseed_test < /tmp/test_backup.sql

# 3. 데이터 무결성 검증
psql -U postgres dreamseed_test <<EOF
SELECT COUNT(*) FROM users;
SELECT COUNT(*) FROM questions;
SELECT COUNT(*) FROM test_results;
EOF

# 4. 테스트 DB 삭제
psql -U postgres -c "DROP DATABASE dreamseed_test;"

echo "✅ 백업 복구 테스트 완료"

# 5. 결과 Slack 알림
if [ $? -eq 0 ]; then
    curl -X POST $SLACK_WEBHOOK -d '{"text":"✅ 월간 백업 복구 테스트 성공"}'
else
    curl -X POST $SLACK_WEBHOOK -d '{"text":"❌ 백업 복구 테스트 실패! 긴급 점검 필요"}'
fi
```

---

## 📞 C) 온콜 가이드

### 1️⃣ 온콜 로테이션

```yaml
1주차: 엔지니어 A (백엔드)
2주차: 엔지니어 B (인프라)
3주차: 엔지니어 C (백엔드)
4주차: 엔지니어 D (인프라)

백업 온콜: CTO (24/7)
```

### 2️⃣ 알람 수신

**Slack 채널**:
- `#incidents-critical` (P0, 즉시 응답)
- `#incidents-high` (P1, 30분 내)
- `#incidents-medium` (P2, 업무시간)

**PagerDuty 설정**:

```yaml
P0 (Critical):
  - SMS: 즉시
  - 전화: 5분 후 (미응답 시)
  - 에스컬레이션: 10분 후 CTO

P1 (High):
  - Slack: 즉시
  - SMS: 15분 후 (미응답 시)
  - 에스컬레이션: 30분 후 CTO

P2 (Medium):
  - Slack만 (업무시간)
```

### 3️⃣ 인시던트 대응 절차

```markdown
# 인시던트 대응 체크리스트

## 1. 인지 (0~2분)
- [ ] Slack/PagerDuty 알람 확인
- [ ] 심각도 판단 (P0/P1/P2)
- [ ] 인시던트 채널 생성 (#incident-YYYYMMDD-N)

## 2. 초기 대응 (2~5분)
- [ ] Grafana 대시보드 확인
- [ ] 에러 로그 확인 (Loki)
- [ ] 영향 범위 파악 (전체/부분)
- [ ] 상태 페이지 업데이트

## 3. 완화 조치 (5~15분)
- [ ] 긴급 스크립트 실행 (rollback/failover)
- [ ] Read-only 모드 전환 (필요 시)
- [ ] 사용자 공지 (앱/이메일)

## 4. 근본 원인 분석 (15분~)
- [ ] 로그 상세 분석
- [ ] 재현 시도
- [ ] 원인 특정

## 5. 복구 (원인 파악 후)
- [ ] 수정 패치 적용
- [ ] 테스트 (스테이징)
- [ ] 프로덕션 배포
- [ ] 검증

## 6. 사후 조치 (복구 후)
- [ ] 포스트모템 작성 (24시간 내)
- [ ] 재발 방지 액션 아이템
- [ ] 모니터링/알람 개선
- [ ] 문서 업데이트
```

### 4️⃣ 인시던트 커뮤니케이션

**Slack 템플릿**:

```markdown
🚨 **인시던트 #INC-20251111-001**

**심각도**: P0 (Critical)
**상태**: 🔍 Investigating
**영향**: 전체 사용자 로그인 불가
**시작 시간**: 2025-11-11 14:23 KST

**타임라인**:
- 14:23 - 인시던트 감지
- 14:25 - 온콜 엔지니어 응답
- 14:28 - DB 장애 확인
- 14:30 - Read Replica로 전환 (읽기 전용)
- 14:45 - Primary DB 복구 중...

**다음 업데이트**: 15:00 또는 상태 변경 시

담당: @engineer-oncall
지원: @cto
```

---

## 📊 D) DR 메트릭 & 대시보드

### 1️⃣ DR 메트릭

```yaml
백업 성공률:
  - 목표: 100%
  - 측정: 일일 백업 성공 횟수 / 시도 횟수
  
백업 복구 테스트 성공률:
  - 목표: 100%
  - 측정: 월간 복구 테스트 성공

평균 복구 시간 (MTTR):
  - 목표: < 1시간
  - 측정: 인시던트 시작 → 복구 완료 시간
  
인시던트 빈도 (MTBF):
  - 목표: > 720시간 (30일)
  - 측정: 인시던트 간 평균 시간
```

### 2️⃣ DR 대시보드 (Grafana)

```json
{
  "dashboard": {
    "title": "재해 복구 모니터링",
    "panels": [
      {
        "title": "백업 상태",
        "type": "stat",
        "targets": [{
          "expr": "backup_success_total / backup_attempt_total"
        }],
        "thresholds": [
          {"value": 0.95, "color": "red"},
          {"value": 0.99, "color": "yellow"},
          {"value": 1.0, "color": "green"}
        ]
      },
      {
        "title": "최근 백업 시간",
        "type": "stat",
        "targets": [{
          "expr": "time() - backup_last_success_timestamp"
        }],
        "unit": "s",
        "thresholds": [
          {"value": 86400, "color": "green"},
          {"value": 172800, "color": "yellow"},
          {"value": 259200, "color": "red"}
        ]
      },
      {
        "title": "인시던트 이력",
        "type": "table",
        "targets": [{
          "expr": "incident_log"
        }]
      },
      {
        "title": "MTTR 추이",
        "type": "graph",
        "targets": [{
          "expr": "avg_over_time(incident_resolution_time[30d])"
        }]
      }
    ]
  }
}
```

---

## 🔥 E) 인시던트 시나리오 훈련

### Fire Drill (분기별)

```yaml
목표: DR 절차 숙지 및 개선

시나리오 1: DB 장애 (2시간)
  - 09:00: 훈련 시작 (예고 없음)
  - 09:02: DB 강제 중단
  - 09:05: 온콜 응답 확인
  - 09:15: Failover 완료 목표
  - 11:00: 복구 완료 및 회고

시나리오 2: 전체 서버 다운 (4시간)
  - 전원 차단 시뮬레이션
  - Full DR 프로세스 실행
  - 클라우드로 완전 전환

시나리오 3: 랜섬웨어 공격
  - 데이터 암호화 가정
  - 백업에서 완전 복구
  - 보안 강화
```

---

## 📝 F) 포스트모템 템플릿

```markdown
# 인시던트 포스트모템: #INC-YYYYMMDD-N

## 기본 정보
- 날짜: YYYY-MM-DD
- 심각도: P0/P1/P2
- 담당: @engineer
- 영향: X명 사용자, Y시간 다운타임

## 요약
한 문장으로 무슨 일이 있었는지

## 타임라인
| 시간 | 이벤트 | 담당자 |
|------|--------|--------|
| 14:23 | 알람 발생 | System |
| 14:25 | 온콜 응답 | @engineer |
| 14:30 | 원인 파악 | @engineer |
| 14:45 | 복구 완료 | @engineer |

## 근본 원인
기술적 상세 설명

## 영향
- 영향받은 사용자: X명
- 다운타임: Y시간 Z분
- 매출 손실: $W
- 평판 손상: 추정치

## 해결 방법
무엇을 어떻게 고쳤는지

## 재발 방지
- [ ] 액션 아이템 1 (담당: @A, 기한: MM/DD)
- [ ] 액션 아이템 2 (담당: @B, 기한: MM/DD)
- [ ] 모니터링 개선 (담당: @C, 기한: MM/DD)

## 교훈
### 잘한 점
- 빠른 응답 (2분 내)
- 명확한 커뮤니케이션

### 개선할 점
- 백업 복구 속도 (30분 → 15분)
- 알람 규칙 세밀화

## 참고
- Grafana 대시보드: [링크]
- Slack 스레드: [링크]
- 관련 PR: [링크]
```

---

## ✅ G) DR 체크리스트

### 일일 체크리스트
- [ ] 백업 성공 확인 (Slack 알림)
- [ ] 디스크 사용률 < 80%
- [ ] DB Replica 동기화 확인

### 주간 체크리스트
- [ ] WAL 아카이브 누락 확인
- [ ] Backblaze B2 스토리지 용량
- [ ] DR 문서 업데이트

### 월간 체크리스트
- [ ] 백업 복구 테스트 실행
- [ ] 온콜 로테이션 업데이트
- [ ] 인시던트 리뷰 회의
- [ ] DR 훈련 계획

### 분기별 체크리스트
- [ ] Fire Drill 실행
- [ ] DR 플랜 전체 검토
- [ ] Cloud SQL DR 인스턴스 테스트
- [ ] 비용 최적화 검토

---

## 🎯 H) 다음 단계

DR 플랜이 완성되었습니다! 이제 실행 단계입니다:

### 즉시 구현 (1주)
- [ ] 일일 백업 스크립트 배포
- [ ] Slack 알람 채널 생성
- [ ] 온콜 로테이션 설정

### 단기 (1개월)
- [ ] WAL 아카이빙 활성화
- [ ] 첫 Fire Drill 실행
- [ ] DR 대시보드 구축

### 중기 (3개월)
- [ ] Cloud SQL DR 인스턴스 준비
- [ ] 분기별 훈련 루틴 확립
- [ ] RTO/RPO 달성 검증

---

## 📚 관련 문서

**마스터플랜 3부작** 완성! 🎉

1. **ARCHITECTURE_MASTERPLAN.md**: 전체 설계
2. **SCALING_STRATEGY.md**: 확장 전략
3. **DISASTER_RECOVERY.md** (현재): 재해 복구

**실행 문서**:
4. **RUNBOOK.md** (다음): 일상 운영 절차
5. **ONCALL_GUIDE.md** (다음): 온콜 상세 가이드
6. **SECURITY_POLICY.md** (다음): 보안 정책

---

**DreamSeedAI 100만 유저 신도시, 완벽한 설계도 완성!** 🏗️✨

**"이제 건설만 남았다!"** 🚀

---

**작성**: GitHub Copilot  
**날짜**: 2025년 11월 11일  
**버전**: 1.0  
**이전**: [SCALING_STRATEGY.md](./SCALING_STRATEGY.md)
