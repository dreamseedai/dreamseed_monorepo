# DreamSeed Alert Threader - All Languages Advanced

Alertmanager webhook을 받아서 Slack Bot API로 고급 스레드 메시지를 전송하는 다중 언어 래퍼 서비스입니다.

## 🚀 지원 언어

- **Python (FastAPI)**: 비동기 처리, 타입 힌트, 자동 문서화
- **Node.js (Express)**: 가벼운 런타임, npm 생태계
- **Go**: 고성능, 단일 바이너리, 낮은 메모리 사용량

## ✨ 고급 기능

- **영속 저장소**: 파일 또는 Redis 기반 thread_ts 저장
- **Slack Block Kit**: 구조화된 메시지 레이아웃
- **Attachments**: 컬러 강조 및 필드 포맷팅
- **고급 포맷팅**: 헤더, 필드, 컨텍스트, 시간 정보
- **Runbook 지원**: 클릭 가능한 링크
- **통계 모니터링**: 저장소별 성능 지표
- **다중 언어**: 동일한 기능을 3가지 언어로 제공

## 📁 구조

```
alert-threader/
├── python-advanced/                    # Python FastAPI 고급 버전
│   ├── app.py                         # 메인 애플리케이션
│   └── requirements.txt               # Python 의존성
├── nodejs-advanced/                   # Node.js Express 고급 버전
│   ├── index.js                       # 메인 애플리케이션
│   └── package.json                   # Node.js 의존성
├── go-advanced/                       # Go 고급 버전
│   ├── main.go                        # 메인 애플리케이션
│   └── go.mod                         # Go 모듈
├── systemd/                           # systemd 서비스 파일
│   ├── alert-threader-advanced.service
│   ├── alert-threader-nodejs-advanced.service
│   └── alert-threader-go-advanced.service
├── install-all-advanced.sh            # 통합 설치 스크립트
├── test-all-advanced.sh               # 통합 테스트 스크립트
├── setup-redis.sh                     # Redis 설정 스크립트
└── README-all-advanced.md             # 이 문서
```

## 🛠️ 설치

### 1. 통합 설치 (권장)

```bash
cd alert-threader
chmod +x install-all-advanced.sh
sudo ./install-all-advanced.sh
```

설치 과정에서 다음을 선택할 수 있습니다:
- 사용할 언어 (Python/Node.js/Go/모든 언어)
- 저장소 타입 (파일/Redis)
- Slack Bot Token
- Slack Channel ID
- 환경 설정

### 2. 개별 언어 설치

#### Python 고급 버전
```bash
cd alert-threader
sudo ./install-advanced.sh
# 언어 선택: 1 (Python)
```

#### Node.js 고급 버전
```bash
cd alert-threader
sudo ./install-advanced.sh
# 언어 선택: 2 (Node.js)
```

#### Go 고급 버전
```bash
cd alert-threader
sudo ./install-advanced.sh
# 언어 선택: 3 (Go)
```

### 3. Redis 설정 (Redis 저장소 선택 시)

```bash
chmod +x setup-redis.sh
sudo ./setup-redis.sh
```

## ⚙️ 설정

### 1. 환경 변수

#### 파일 저장소 (기본)
```bash
sudo mkdir -p /etc/systemd/system/alert-threader-<language>.service.d
cat << EOF | sudo tee /etc/systemd/system/alert-threader-<language>.service.d/override.conf
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
sudo mkdir -p /etc/systemd/system/alert-threader-<language>.service.d
cat << EOF | sudo tee /etc/systemd/system/alert-threader-<language>.service.d/override.conf
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

### 통합 테스트
```bash
chmod +x test-all-advanced.sh
./test-all-advanced.sh
```

### 개별 언어 테스트
```bash
# Python
chmod +x test-advanced.sh
./test-advanced.sh

# Node.js
chmod +x test-advanced.sh
./test-advanced.sh

# Go
chmod +x test-advanced.sh
./test-advanced.sh
```

## 📊 API 엔드포인트

모든 언어 버전에서 동일한 API를 제공합니다:

### GET /health
서비스 상태 및 저장소 연결 상태 확인

### GET /stats
상세 통계 정보 조회

### POST /alert
Alertmanager webhook 엔드포인트

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

## 🔧 언어별 특징

### Python (FastAPI)
- **비동기 처리**: `async/await` 지원
- **자동 문서화**: Swagger UI 제공
- **타입 힌트**: 코드 안정성 향상
- **의존성 관리**: pip + requirements.txt

### Node.js (Express)
- **가벼운 런타임**: 빠른 시작 시간
- **npm 생태계**: 풍부한 라이브러리
- **이벤트 기반**: 높은 동시성
- **ES 모듈**: 최신 JavaScript 기능

### Go
- **고성능**: 낮은 CPU/메모리 사용량
- **단일 바이너리**: 배포 간편
- **정적 컴파일**: 의존성 없음
- **동시성**: goroutine 기반

## 🚨 문제 해결

### 1. 서비스 시작 실패
```bash
# 로그 확인
sudo journalctl -u alert-threader-<language> -f

# 환경 변수 확인
sudo systemctl show alert-threader-<language> --property=Environment

# 의존성 확인
# Python: python3 -c "import redis; print('Redis OK')"
# Node.js: node -e "console.log('Node.js OK')"
# Go: go version
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

## 📈 성능 비교

| 언어 | 메모리 사용량 | CPU 사용량 | 시작 시간 | 동시성 |
|------|---------------|------------|-----------|--------|
| Python | 중간 | 중간 | 느림 | 높음 |
| Node.js | 낮음 | 낮음 | 빠름 | 매우 높음 |
| Go | 매우 낮음 | 매우 낮음 | 매우 빠름 | 높음 |

## 🔄 언어 전환

### 서비스 중지
```bash
# 현재 실행 중인 서비스 중지
sudo systemctl stop alert-threader-<current-language>
```

### 서비스 시작
```bash
# 다른 언어 서비스 시작
sudo systemctl start alert-threader-<new-language>
```

### 서비스 상태 확인
```bash
# 모든 언어 서비스 상태 확인
for lang in python nodejs go; do
    echo "=== $lang ==="
    sudo systemctl status alert-threader-$lang --no-pager
done
```

## 📊 모니터링

### 서비스 상태
```bash
# 실행 중인 서비스 확인
systemctl list-units --type=service | grep alert-threader

# 포트 사용 확인
netstat -tlnp | grep :9009
```

### 성능 지표
```bash
# 헬스체크
curl http://localhost:9009/health | jq .

# 통계
curl http://localhost:9009/stats | jq .

# 캐시 상태
curl http://localhost:9009/cache | jq .
```

### 로그 모니터링
```bash
# 실시간 로그
sudo journalctl -u alert-threader-<language> -f

# 최근 로그
sudo journalctl -u alert-threader-<language> --no-pager -n 50
```

## 🔄 업그레이드

### 통합 업그레이드
```bash
# 새 버전 복사
sudo cp -r alert-threader/*-advanced/* /opt/alert-threader/*-advanced/

# 의존성 업데이트
# Python: cd /opt/alert-threader/python-advanced && sudo pip3 install -r requirements.txt --upgrade
# Node.js: cd /opt/alert-threader/nodejs-advanced && sudo npm update
# Go: cd /opt/alert-threader/go-advanced && go mod tidy

# 서비스 재시작
sudo systemctl restart alert-threader-<language>
```

## 🗑️ 제거

### 개별 언어 제거
```bash
# 서비스 중지 및 비활성화
sudo systemctl stop alert-threader-<language>
sudo systemctl disable alert-threader-<language>

# 파일 제거
sudo rm -rf /opt/alert-threader/<language>-advanced
sudo rm /etc/systemd/system/alert-threader-<language>.service

# systemd 데몬 리로드
sudo systemctl daemon-reload
```

### 전체 제거
```bash
# 모든 서비스 중지
for lang in python nodejs go; do
    sudo systemctl stop alert-threader-$lang 2>/dev/null || true
    sudo systemctl disable alert-threader-$lang 2>/dev/null || true
done

# 파일 제거
sudo rm -rf /opt/alert-threader
sudo rm -rf /var/lib/alert-threader
sudo rm /etc/systemd/system/alert-threader-*.service

# Redis 데이터 제거 (Redis 저장소 사용 시)
redis-cli flushdb

# systemd 데몬 리로드
sudo systemctl daemon-reload
```

## 📄 라이선스

MIT License

