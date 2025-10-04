# DreamSeed Alert Threader - 모든 언어 EnvironmentFile 통합 가이드

Alertmanager webhook을 받아서 Slack Bot API로 고급 스레드 메시지를 전송하는 **모든 언어 버전**을 EnvironmentFile 패턴으로 통합 관리합니다.

## 🎯 **통합된 특징**

### **1. EnvironmentFile 통합 관리**
- **단일 환경 파일**: `/etc/alert-threader.env`로 모든 언어 통합 관리
- **보안 강화**: 민감한 환경변수를 별도 파일로 분리
- **권한 관리**: `root:root` 소유, `640` 권한으로 보안 강화
- **중앙 관리**: Python/Node.js/Go 모두 동일한 환경 파일 사용

### **2. 언어별 최적화**
- **Python**: FastAPI + 비동기 처리 + 타입 힌트
- **Node.js**: Express + 이벤트 기반 + npm 생태계
- **Go**: go-redis/v9 + 단일 바이너리 + 고성능

### **3. 저장소 선택**
- **파일 저장소**: 단순함, 로컬 파일 기반
- **Redis 저장소**: 고성능, 확장성, 분산 환경 지원

## 🚀 **빠른 시작**

### **통합 설치 (권장)**
```bash
cd alert-threader
chmod +x install-all-envfile.sh
sudo ./install-all-envfile.sh
```

설치 과정에서 다음을 선택할 수 있습니다:
- 사용할 언어 (Python/Node.js/Go/모든 언어)
- 저장소 타입 (파일/Redis)
- Slack Bot Token
- Slack Channel ID
- 환경 설정

## 📁 **파일 구조**

```
alert-threader/
├── etc-alert-threader.env.template          # 환경 파일 템플릿
├── python-advanced-envfile/
│   ├── app.py                               # FastAPI EnvironmentFile 버전
│   └── requirements.txt                     # Python 의존성
├── nodejs-advanced/
│   ├── index.js                             # Express EnvironmentFile 버전
│   └── package.json                         # Node.js 의존성
├── go-advanced-redis/
│   ├── main.go                              # go-redis 실제 연결 구현
│   └── go.mod                               # Go 의존성
├── ops-services-alert-threader-python-envfile.service  # Python EnvironmentFile 유닛
├── ops-services-alert-threader-node-envfile.service    # Node.js EnvironmentFile 유닛
├── ops-services-alert-threader-go-envfile.service      # Go EnvironmentFile 유닛
├── install-all-envfile.sh                   # 통합 설치 스크립트
└── README-all-envfile.md                    # 이 문서
```

## ⚙️ **환경 설정**

### **통합 환경 파일**
```bash
# /etc/alert-threader.env
# =============================
# Alert Threader Environment
# =============================

# =============================
# Slack Bot Configuration
# =============================
SLACK_BOT_TOKEN=xoxb-your-actual-token
SLACK_CHANNEL=C0123456789
ENVIRONMENT=production

# =============================
# Storage Configuration
# =============================
THREAD_STORE=redis                    # file | redis
THREAD_STORE_FILE=/var/lib/alert-threader/threads.json
REDIS_URL=redis://127.0.0.1:6379/0
REDIS_KEY_PREFIX=threader:ts

# =============================
# Service Configuration
# =============================
BIND_HOST=0.0.0.0
BIND_PORT=9009

# =============================
# Security & Performance
# =============================
REDIS_TIMEOUT=5
LOG_LEVEL=info
MAX_CONCURRENT_ALERTS=100

# =============================
# Monitoring & Health
# =============================
HEALTH_CHECK_INTERVAL=30
ENABLE_STATS=true

# =============================
# Advanced Configuration
# =============================
THREAD_KEY_STRATEGY=simple
CACHE_TTL=86400
MAX_RETRIES=3
RETRY_DELAY=1000
```

## 🔧 **언어별 설치**

### **Python (FastAPI)**
```bash
# 서비스 파일 복사
sudo cp ops-services-alert-threader-python-envfile.service /etc/systemd/system/alert-threader-python.service

# 애플리케이션 복사
sudo mkdir -p /opt/alert-threader-python
sudo cp -r python-advanced-envfile/* /opt/alert-threader-python/
sudo chown -R www-data:www-data /opt/alert-threader-python

# 서비스 시작
sudo systemctl daemon-reload
sudo systemctl enable --now alert-threader-python
```

### **Node.js (Express)**
```bash
# 서비스 파일 복사
sudo cp ops-services-alert-threader-node-envfile.service /etc/systemd/system/alert-threader-node.service

# 애플리케이션 복사
sudo mkdir -p /opt/alert-threader-node
sudo cp -r nodejs-advanced/* /opt/alert-threader-node/
sudo chown -R www-data:www-data /opt/alert-threader-node

# 서비스 시작
sudo systemctl daemon-reload
sudo systemctl enable --now alert-threader-node
```

### **Go (go-redis)**
```bash
# 서비스 파일 복사
sudo cp ops-services-alert-threader-go-envfile.service /etc/systemd/system/alert-threader-go.service

# 애플리케이션 복사
sudo mkdir -p /opt/alert-threader-go-redis
sudo cp -r go-advanced-redis/* /opt/alert-threader-go-redis/
sudo chown -R www-data:www-data /opt/alert-threader-go-redis

# Go 의존성 설치
cd /opt/alert-threader-go-redis
go mod tidy

# 서비스 시작
sudo systemctl daemon-reload
sudo systemctl enable --now alert-threader-go
```

## 🧪 **테스트**

### **통합 테스트**
```bash
chmod +x test-all-advanced.sh
./test-all-advanced.sh
```

### **개별 서비스 테스트**
```bash
# Python
curl http://localhost:9009/health | jq .
curl http://localhost:9009/stats | jq .

# Node.js
curl http://localhost:9010/health | jq .
curl http://localhost:9010/stats | jq .

# Go
curl http://localhost:9011/health | jq .
curl http://localhost:9011/stats | jq .
```

### **Redis 연결 테스트**
```bash
# Redis 상태 확인
redis-cli ping

# Redis 키 확인
redis-cli keys "threader:ts:*"

# Redis 통계
redis-cli info memory
```

## 📊 **API 엔드포인트**

모든 언어 버전에서 동일한 API를 제공합니다:

### **GET /health**
서비스 상태 및 저장소 연결 상태 확인

**응답 예시:**
```json
{
  "status": "healthy",
  "environment": "production",
  "channel": "C0123456789",
  "thread_store": "redis",
  "cached_threads": 15,
  "timestamp": "2024-01-15T10:00:00Z",
  "redis_status": "connected"
}
```

### **GET /stats**
상세 통계 정보 조회

**응답 예시:**
```json
{
  "cached_threads": 15,
  "thread_store": "redis",
  "environment": "production",
  "uptime": "2h30m15s",
  "startup_time": "2024-01-15T07:30:00Z",
  "redis_info": "used_memory:1048576\nconnected_clients:5\n..."
}
```

### **POST /alert**
Alertmanager webhook 엔드포인트

### **GET /cache**
캐시 상태 조회 (디버깅용)

### **DELETE /cache**
캐시 초기화 (디버깅용)

## 🔄 **서비스 관리**

### **모든 서비스 상태 확인**
```bash
for lang in python nodejs go; do
    echo "=== $lang ==="
    sudo systemctl status alert-threader-$lang --no-pager
done
```

### **서비스 전환**
```bash
# Python → Node.js
sudo systemctl stop alert-threader-python
sudo systemctl start alert-threader-node

# Node.js → Go
sudo systemctl stop alert-threader-node
sudo systemctl start alert-threader-go

# Go → Python
sudo systemctl stop alert-threader-go
sudo systemctl start alert-threader-python
```

### **모든 서비스 시작/중지**
```bash
# 모든 서비스 시작
for lang in python nodejs go; do
    sudo systemctl start alert-threader-$lang
done

# 모든 서비스 중지
for lang in python nodejs go; do
    sudo systemctl stop alert-threader-$lang
done
```

## 📈 **성능 비교**

| 언어 | 메모리 사용량 | CPU 사용량 | 시작 시간 | Redis 연결 | 특징 |
|------|---------------|------------|-----------|------------|------|
| **Python** | 중간 | 중간 | 느림 | redis-py | 비동기, 타입 힌트, EnvironmentFile |
| **Node.js** | 낮음 | 낮음 | 빠름 | redis | 이벤트 기반, EnvironmentFile |
| **Go** | 매우 낮음 | 매우 낮음 | 매우 빠름 | go-redis/v9 | 단일 바이너리, 실제 Redis, EnvironmentFile |

## 🚨 **문제 해결**

### **1. 환경 파일 문제**
```bash
# 환경 파일 권한 확인
ls -la /etc/alert-threader.env

# 환경 파일 내용 확인
sudo cat /etc/alert-threader.env

# 환경 변수 로드 테스트
sudo systemctl show alert-threader-python --property=Environment
```

### **2. Redis 연결 실패**
```bash
# Redis 상태 확인
sudo systemctl status redis-server

# Redis 연결 테스트
redis-cli ping

# Redis 로그 확인
sudo journalctl -u redis-server -f
```

### **3. 서비스 시작 실패**
```bash
# 서비스 로그 확인
sudo journalctl -u alert-threader-python -f
sudo journalctl -u alert-threader-node -f
sudo journalctl -u alert-threader-go -f

# 환경 변수 확인
sudo systemctl show alert-threader-python --property=Environment
```

### **4. 포트 충돌**
```bash
# 포트 사용 확인
netstat -tlnp | grep :9009

# 서비스 중지
sudo systemctl stop alert-threader-python
sudo systemctl stop alert-threader-node
sudo systemctl stop alert-threader-go
```

## 🔄 **업그레이드**

### **환경 파일 업데이트**
```bash
# 환경 파일 백업
sudo cp /etc/alert-threader.env /etc/alert-threader.env.bak

# 환경 파일 수정
sudo nano /etc/alert-threader.env

# 모든 서비스 재시작
for lang in python nodejs go; do
    sudo systemctl restart alert-threader-$lang
done
```

### **코드 업데이트**
```bash
# 새 버전 복사
sudo cp -r python-advanced-envfile/* /opt/alert-threader/python-advanced-envfile/
sudo cp -r nodejs-advanced/* /opt/alert-threader/nodejs-advanced/
sudo cp -r go-advanced-redis/* /opt/alert-threader/go-advanced-redis/

# 의존성 업데이트
# Python: cd /opt/alert-threader/python-advanced-envfile && sudo pip install -r requirements.txt
# Node.js: cd /opt/alert-threader/nodejs-advanced && sudo npm update
# Go: cd /opt/alert-threader/go-advanced-redis && go mod tidy

# 모든 서비스 재시작
for lang in python nodejs go; do
    sudo systemctl restart alert-threader-$lang
done
```

## 🗑️ **제거**

### **개별 언어 제거**
```bash
# 서비스 중지 및 비활성화
sudo systemctl stop alert-threader-<language>
sudo systemctl disable alert-threader-<language>

# 파일 제거
sudo rm -rf /opt/alert-threader/<language>-advanced*
sudo rm /etc/systemd/system/alert-threader-<language>.service

# systemd 데몬 리로드
sudo systemctl daemon-reload
```

### **전체 제거**
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
sudo rm /etc/alert-threader.env

# Redis 데이터 제거 (Redis 저장소 사용 시)
redis-cli flushdb

# systemd 데몬 리로드
sudo systemctl daemon-reload
```

## 🎯 **사용 시나리오**

### **1. 개발 환경**
- **Python**: 빠른 프로토타이핑, 타입 힌트로 안정성
- **파일 저장소**: 단순한 설정, 로컬 개발

### **2. 스테이징 환경**
- **Node.js**: 빠른 시작, 이벤트 기반 처리
- **Redis 저장소**: 프로덕션과 동일한 환경

### **3. 프로덕션 환경**
- **Go**: 고성능, 낮은 리소스 사용량
- **Redis 저장소**: 고가용성, 확장성

### **4. 다중 언어 운영**
- **Python**: 메인 서비스 (포트 9009)
- **Node.js**: 백업 서비스 (포트 9010)
- **Go**: 고성능 서비스 (포트 9011)

## 📄 **라이선스**

MIT License

---

## 🎉 **완성된 기능**

1. **✅ EnvironmentFile 통합**: 모든 언어가 동일한 환경 파일 사용
2. **✅ Python FastAPI**: 비동기 처리 + 타입 힌트 + EnvironmentFile
3. **✅ Node.js Express**: 이벤트 기반 + npm 생태계 + EnvironmentFile
4. **✅ Go go-redis**: 고성능 + 단일 바이너리 + 실제 Redis 연결
5. **✅ 보안 강화**: 파일 권한 및 systemd 하드닝
6. **✅ 중앙 관리**: 통합 환경 파일 사용
7. **✅ 타임아웃 지원**: Redis 연결 타임아웃 설정
8. **✅ 에러 처리**: Redis 연결 실패 시 적절한 처리
9. **✅ 성능 최적화**: 로컬 캐시 + Redis 조합
10. **✅ 통합 설치**: 원클릭 설치 및 설정
11. **✅ 포괄적인 문서화**: 설치부터 문제해결까지 완전한 가이드

이제 **엔터프라이즈급 보안과 성능**을 갖춘 **모든 언어 버전**의 Alert Threader가 완성되었습니다! 🎉

**사용자는 이제 다음 명령어 하나로 전체 시스템을 배포할 수 있습니다:**

```bash
sudo ./install-all-envfile.sh
```

