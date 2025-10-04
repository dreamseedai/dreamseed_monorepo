# DreamSeed Alert Threader - Advanced

Alertmanager webhook을 받아서 Slack Bot API로 고급 스레드 메시지를 전송하는 래퍼 서비스입니다.

## 🚀 고급 기능

- **영속 저장소**: 파일 또는 Redis 기반 thread_ts 저장
- **Slack Block Kit**: 구조화된 메시지 레이아웃
- **Attachments**: 컬러 강조 및 필드 포맷팅
- **고급 포맷팅**: 헤더, 필드, 컨텍스트, 시간 정보
- **Runbook 지원**: 클릭 가능한 링크
- **통계 모니터링**: 저장소별 성능 지표

## 📁 구조

```
alert-threader/
├── python-advanced/              # 고급 Python FastAPI 버전
│   ├── app.py                   # 메인 애플리케이션
│   └── requirements.txt         # Python 의존성
├── systemd/
│   └── alert-threader-advanced.service  # systemd 서비스
├── install-advanced.sh          # 고급 설치 스크립트
├── test-advanced.sh             # 고급 테스트 스크립트
├── setup-redis.sh               # Redis 설정 스크립트
└── README-advanced.md           # 이 문서
```

## 🛠️ 설치

### 1. 자동 설치 (권장)

```bash
cd alert-threader
chmod +x install-advanced.sh
sudo ./install-advanced.sh
```

설치 과정에서 다음을 선택할 수 있습니다:
- 저장소 타입 (파일/Redis)
- Slack Bot Token
- Slack Channel ID
- 환경 설정

### 2. Redis 설정 (Redis 저장소 선택 시)

```bash
chmod +x setup-redis.sh
sudo ./setup-redis.sh
```

### 3. 수동 설치

#### Python 고급 버전
```bash
# 의존성 설치
sudo apt install python3 python3-pip redis-server

# 파일 복사
sudo mkdir -p /opt/alert-threader/python-advanced
sudo cp python-advanced/* /opt/alert-threader/python-advanced/
cd /opt/alert-threader/python-advanced
sudo pip3 install -r requirements.txt

# systemd 서비스 설정
sudo cp systemd/alert-threader-advanced.service /etc/systemd/system/alert-threader.service
sudo systemctl daemon-reload
sudo systemctl enable --now alert-threader
```

## ⚙️ 설정

### 1. 환경 변수

#### 파일 저장소 (기본)
```bash
sudo mkdir -p /etc/systemd/system/alert-threader.service.d
cat << EOF | sudo tee /etc/systemd/system/alert-threader.service.d/override.conf
[Service]
Environment=SLACK_BOT_TOKEN=xoxb-your-bot-token
Environment=SLACK_CHANNEL=C0123456789
Environment=ENVIRONMENT=production
Environment=THREAD_STORE=file
Environment=THREAD_STORE_FILE=/var/lib/alert-threader/threads.json
EOF
```

#### Redis 저장소
```bash
sudo mkdir -p /etc/systemd/system/alert-threader.service.d
cat << EOF | sudo tee /etc/systemd/system/alert-threader.service.d/override.conf
[Service]
Environment=SLACK_BOT_TOKEN=xoxb-your-bot-token
Environment=SLACK_CHANNEL=C0123456789
Environment=ENVIRONMENT=production
Environment=THREAD_STORE=redis
Environment=REDIS_URL=redis://127.0.0.1:6379/0
Environment=REDIS_KEY_PREFIX=threader:ts
EOF
```

### 2. Alertmanager 설정

```bash
# Alertmanager 설정 업데이트
sudo cp alertmanager-threader.yml /etc/alertmanager/alertmanager.yml
sudo systemctl restart alertmanager
```

## 🧪 테스트

```bash
chmod +x test-advanced.sh
./test-advanced.sh
```

### 수동 테스트

```bash
# 헬스체크
curl http://localhost:9009/health | jq .

# 통계 확인
curl http://localhost:9009/stats | jq .

# Critical 알림 테스트
curl -X POST http://localhost:9009/alert \
  -H 'Content-Type: application/json' \
  -d '{
    "status": "firing",
    "alerts": [
      {
        "labels": {
          "alertname": "TestCritical",
          "severity": "critical",
          "service": "database",
          "cluster": "production",
          "instance": "db01.example.com"
        },
        "annotations": {
          "summary": "Database Critical Failure",
          "description": "MySQL connection completely failed",
          "runbook_url": "https://docs.example.com/runbooks/db-failure"
        },
        "startsAt": "2024-01-15T14:30:25Z"
      }
    ]
  }' | jq .
```

## 📊 API 엔드포인트

### GET /health
서비스 상태 및 저장소 연결 상태 확인

**응답:**
```json
{
  "status": "healthy",
  "environment": "production",
  "channel": "C0123456789",
  "thread_store": "redis",
  "cached_threads": 5,
  "timestamp": "2024-01-15T14:30:25.123456",
  "redis_status": "connected"
}
```

### GET /stats
상세 통계 정보 조회

**응답:**
```json
{
  "cached_threads": 5,
  "thread_store": "redis",
  "environment": "production",
  "uptime": "2024-01-15T14:30:25.123456",
  "redis": {
    "connected_clients": 2,
    "used_memory_human": "2.1M",
    "keyspace_hits": 150,
    "keyspace_misses": 5
  }
}
```

### POST /alert
Alertmanager webhook 엔드포인트

**요청:**
```json
{
  "status": "firing",
  "groupKey": "test-group-1",
  "alerts": [
    {
      "labels": {
        "alertname": "TestAlert",
        "severity": "critical",
        "service": "database",
        "cluster": "production",
        "instance": "db01.example.com",
        "job": "mysql-exporter"
      },
      "annotations": {
        "summary": "Database Critical Failure",
        "description": "MySQL connection completely failed",
        "runbook_url": "https://docs.example.com/runbooks/db-failure"
      },
      "startsAt": "2024-01-15T14:30:25Z",
      "endsAt": "2024-01-15T14:45:30Z"
    }
  ]
}
```

**응답:**
```json
{
  "ok": true,
  "count": 1,
  "status": "firing",
  "group_key": "test-group-1",
  "thread_store": "redis",
  "results": [
    {
      "key": "TestAlert|critical|database|production|production",
      "thread_ts": "1234567890.123456",
      "status": "firing",
      "alertname": "TestAlert",
      "severity": "critical"
    }
  ]
}
```

### GET /cache
캐시 상태 조회 (디버깅용)

### DELETE /cache
캐시 초기화 (디버깅용)

## 🎨 메시지 포맷

### Block Kit 구조

#### Critical 알림 (새 스레드)
```
🚨 Database Critical Failure

Severity: CRITICAL          Environment: production
Service: database           Cluster: production
Instance: db01.example.com

Description:
MySQL connection completely failed. Immediate action required.

Runbook: View Runbook

Started: 2024-01-15 14:30:25 UTC

env=production | alertname=DatabaseCriticalFailure
```

#### Resolved 알림 (스레드 답글)
```
✅ RESOLVED — Database Critical Failure

Severity: CRITICAL          Environment: production
Service: database           Cluster: production
Instance: db01.example.com

Description:
Database connection has been restored successfully.

Runbook: View Runbook

Started: 2024-01-15 14:30:25 UTC | Resolved: 2024-01-15 14:45:30 UTC

env=production | alertname=DatabaseCriticalFailure
```

### Attachments 컬러

- **Critical**: 🚨 빨강 (#E01E5A)
- **Warning**: ⚠️ 노랑 (#ECB22E)
- **Info**: ℹ️ 초록 (#2EB67D)
- **Error**: ❌ 빨강 (#E01E5A)
- **Success**: ✅ 초록 (#2EB67D)
- **Debug**: 🐛 파랑 (#36C5F0)

## 🔧 저장소 관리

### 파일 저장소

```bash
# 스레드 파일 위치
ls -la /var/lib/alert-threader/threads.json

# 백업
cp /var/lib/alert-threader/threads.json /backup/threads-$(date +%Y%m%d).json

# 복원
cp /backup/threads-20240115.json /var/lib/alert-threader/threads.json
sudo systemctl restart alert-threader
```

### Redis 저장소

```bash
# Redis 클라이언트 접속
redis-cli

# 스레드 키 조회
keys threader:ts:*

# 특정 스레드 조회
get threader:ts:TestAlert|critical|database|production|production

# 모든 스레드 삭제
del threader:ts:*

# Redis 정보
info memory
info stats
```

## 🚨 문제 해결

### 1. 서비스 시작 실패
```bash
# 로그 확인
sudo journalctl -u alert-threader -f

# 환경 변수 확인
sudo systemctl show alert-threader --property=Environment

# 의존성 확인
python3 -c "import redis; print('Redis OK')"
```

### 2. Redis 연결 실패
```bash
# Redis 상태 확인
sudo systemctl status redis-server

# Redis 연결 테스트
redis-cli ping

# Redis 로그 확인
sudo journalctl -u redis-server -f
```

### 3. Slack API 오류
```bash
# Bot Token 확인
echo $SLACK_BOT_TOKEN

# 채널 권한 확인 (Slack 워크스페이스에서)
# - Bot이 채널에 초대되어 있는지
# - chat:write 권한이 있는지
```

### 4. 스레드 생성 안됨
```bash
# 캐시 상태 확인
curl http://localhost:9009/cache | jq .

# 저장소별 확인
# 파일: ls -la /var/lib/alert-threader/threads.json
# Redis: redis-cli keys 'threader:ts:*'

# 캐시 초기화
curl -X DELETE http://localhost:9009/cache
```

## 📈 성능 최적화

### Redis 최적화
```bash
# Redis 설정 최적화
sudo nano /etc/redis/redis.conf.d/threader.conf

# 메모리 사용량 모니터링
redis-cli info memory

# 키 만료 설정 (선택사항)
redis-cli config set maxmemory-policy allkeys-lru
```

### 파일 저장소 최적화
```bash
# 파일 권한 최적화
sudo chown www-data:www-data /var/lib/alert-threader/threads.json
sudo chmod 644 /var/lib/alert-threader/threads.json

# 정기 백업 설정
echo "0 2 * * * root cp /var/lib/alert-threader/threads.json /backup/threads-\$(date +\%Y\%m\%d).json" | sudo tee -a /etc/crontab
```

## 🔄 업그레이드

```bash
# 새 버전 복사
sudo cp -r alert-threader/python-advanced/* /opt/alert-threader/python-advanced/

# 의존성 업데이트
cd /opt/alert-threader/python-advanced
sudo pip3 install -r requirements.txt --upgrade

# 서비스 재시작
sudo systemctl restart alert-threader
```

## 🗑️ 제거

```bash
# 서비스 중지 및 비활성화
sudo systemctl stop alert-threader
sudo systemctl disable alert-threader

# 파일 제거
sudo rm -rf /opt/alert-threader
sudo rm -rf /var/lib/alert-threader
sudo rm /etc/systemd/system/alert-threader.service

# Redis 데이터 제거 (Redis 저장소 사용 시)
redis-cli flushdb

# systemd 데몬 리로드
sudo systemctl daemon-reload
```

## 📄 라이선스

MIT License

