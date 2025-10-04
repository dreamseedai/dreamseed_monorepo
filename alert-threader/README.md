# DreamSeed Alert Threader

Alertmanager webhook을 받아서 Slack Bot API로 스레드 메시지를 전송하는 래퍼 서비스입니다.

## 🚀 특징

- **스레드 지원**: Alertmanager의 기본 Slack 통합이 지원하지 않는 스레드 기능 제공
- **다중 언어**: Python (FastAPI), Node.js (Express), Go 3가지 버전 제공
- **스마트 캐싱**: 알림별로 스레드를 자동 관리
- **Block Kit**: Slack의 Block Kit을 사용한 풍부한 메시지 포맷
- **자동 그룹화**: 같은 알림은 자동으로 스레드로 그룹화

## 📁 구조

```
alert-threader/
├── python/                    # Python FastAPI 버전
│   ├── app.py
│   └── requirements.txt
├── nodejs/                    # Node.js Express 버전
│   ├── index.js
│   └── package.json
├── go/                        # Go 버전
│   ├── main.go
│   └── go.mod
├── systemd/                   # systemd 서비스 파일
│   ├── alert-threader-python.service
│   ├── alert-threader-nodejs.service
│   └── alert-threader-go.service
├── alertmanager-threader.yml  # Alertmanager 설정
├── install.sh                 # 설치 스크립트
├── test.sh                    # 테스트 스크립트
└── README.md
```

## 🛠️ 설치

### 1. 자동 설치 (권장)

```bash
cd alert-threader
chmod +x install.sh
sudo ./install.sh
```

설치 과정에서 다음 정보를 입력해야 합니다:
- 사용할 언어 (Python/Node.js/Go)
- Slack Bot Token (xoxb-...)
- Slack Channel ID (C0123456789)
- 환경 (staging/production)

### 2. 수동 설치

#### Python 버전
```bash
# 의존성 설치
sudo apt install python3 python3-pip

# 파일 복사
sudo mkdir -p /opt/alert-threader/python
sudo cp python/* /opt/alert-threader/python/
cd /opt/alert-threader/python
sudo pip3 install -r requirements.txt

# systemd 서비스 설정
sudo cp systemd/alert-threader-python.service /etc/systemd/system/alert-threader.service
sudo systemctl daemon-reload
sudo systemctl enable --now alert-threader
```

#### Node.js 버전
```bash
# Node.js 설치
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install nodejs

# 파일 복사
sudo mkdir -p /opt/alert-threader/nodejs
sudo cp nodejs/* /opt/alert-threader/nodejs/
cd /opt/alert-threader/nodejs
sudo npm install

# systemd 서비스 설정
sudo cp systemd/alert-threader-nodejs.service /etc/systemd/system/alert-threader.service
sudo systemctl daemon-reload
sudo systemctl enable --now alert-threader
```

#### Go 버전
```bash
# Go 설치
sudo apt install golang-go

# 파일 복사
sudo mkdir -p /opt/alert-threader/go
sudo cp go/* /opt/alert-threader/go/
cd /opt/alert-threader/go
go mod tidy

# systemd 서비스 설정
sudo cp systemd/alert-threader-go.service /etc/systemd/system/alert-threader.service
sudo systemctl daemon-reload
sudo systemctl enable --now alert-threader
```

## ⚙️ 설정

### 1. 환경 변수

```bash
# systemd override 파일 생성
sudo mkdir -p /etc/systemd/system/alert-threader.service.d
cat << EOF | sudo tee /etc/systemd/system/alert-threader.service.d/override.conf
[Service]
Environment=SLACK_BOT_TOKEN=xoxb-your-bot-token
Environment=SLACK_CHANNEL=C0123456789
Environment=ENVIRONMENT=production
Environment=BIND_HOST=0.0.0.0
Environment=BIND_PORT=9009
EOF

sudo systemctl daemon-reload
sudo systemctl restart alert-threader
```

### 2. Alertmanager 설정

```bash
# Alertmanager 설정 업데이트
sudo cp alertmanager-threader.yml /etc/alertmanager/alertmanager.yml
sudo systemctl restart alertmanager
```

## 🧪 테스트

```bash
chmod +x test.sh
./test.sh
```

### 수동 테스트

```bash
# 헬스체크
curl http://localhost:9009/health

# Critical 알림 테스트
curl -X POST http://localhost:9009/alert \
  -H 'Content-Type: application/json' \
  -d '{
    "status": "firing",
    "alerts": [
      {
        "labels": {
          "alertname": "TestAlert",
          "severity": "critical",
          "service": "test"
        },
        "annotations": {
          "summary": "테스트 알림",
          "description": "테스트 설명"
        }
      }
    ]
  }'

# 캐시 상태 확인
curl http://localhost:9009/cache

# 캐시 초기화
curl -X DELETE http://localhost:9009/cache
```

## 📊 API 엔드포인트

### GET /health
서비스 상태 확인

**응답:**
```json
{
  "status": "healthy",
  "environment": "production",
  "channel": "C0123456789",
  "cached_threads": 5
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
        "service": "test"
      },
      "annotations": {
        "summary": "테스트 알림",
        "description": "테스트 설명"
      }
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
  "results": [
    {
      "key": "TestAlert|critical|test|production",
      "thread_ts": "1234567890.123456",
      "status": "firing",
      "alertname": "TestAlert"
    }
  ]
}
```

### GET /cache
캐시 상태 조회 (디버깅용)

### DELETE /cache
캐시 초기화 (디버깅용)

## 🔧 스레드 키 전략

스레드는 다음 키로 구분됩니다:
```
{alertname}|{severity}|{service}|{environment}
```

예시:
- `SQLiteBackupFailed|critical|backup|production`
- `APIHighResponseTime|warning|api|staging`

## 🎨 메시지 포맷

### Critical 알림
```
🚨 [production] **SQLite 백업 실패** (`critical`)

설명: DreamSeed 백업 서비스가 실패 상태입니다

라벨: `alertname=SQLiteBackupFailed` | `severity=critical` | `service=backup`
```

### Resolved 알림
```
✅ [production] **RESOLVED** - SQLite 백업 실패

설명: 백업이 정상적으로 복구되었습니다
```

## 🚨 문제 해결

### 1. 서비스가 시작되지 않음
```bash
# 로그 확인
sudo journalctl -u alert-threader -f

# 환경 변수 확인
sudo systemctl show alert-threader --property=Environment
```

### 2. Slack API 오류
```bash
# Bot Token 확인
echo $SLACK_BOT_TOKEN

# 채널 ID 확인
echo $SLACK_CHANNEL

# 권한 확인 (Slack 워크스페이스에서)
# - Bot이 채널에 초대되어 있는지
# - chat:write 권한이 있는지
```

### 3. 스레드가 생성되지 않음
```bash
# 캐시 상태 확인
curl http://localhost:9009/cache

# 캐시 초기화
curl -X DELETE http://localhost:9009/cache
```

## 📝 로그

```bash
# 실시간 로그
sudo journalctl -u alert-threader -f

# 최근 로그
sudo journalctl -u alert-threader --no-pager -n 50
```

## 🔄 업그레이드

```bash
# 새 버전 복사
sudo cp -r alert-threader/$LANG/* /opt/alert-threader/$LANG/

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
sudo rm /etc/systemd/system/alert-threader.service

# systemd 데몬 리로드
sudo systemctl daemon-reload
```

## 📄 라이선스

MIT License

