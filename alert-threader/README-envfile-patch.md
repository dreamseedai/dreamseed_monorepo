# DreamSeed Alert Threader - EnvironmentFile 분리 & go-redis 패치

Alertmanager webhook을 받아서 Slack Bot API로 고급 스레드 메시지를 전송하는 다중 언어 래퍼 서비스입니다. 이 패치는 **EnvironmentFile 분리**와 **Go go-redis 실제 연결**을 포함합니다.

## 🔐 **주요 개선사항**

### **1. EnvironmentFile 분리**
- **보안 강화**: 민감한 환경변수를 별도 파일로 분리
- **권한 관리**: root 소유, 640 권한으로 보안 강화
- **중앙 관리**: 모든 서비스가 동일한 환경 파일 사용
- **템플릿 제공**: `/etc/alert-threader.env.template` 제공

### **2. Go go-redis 실제 연결**
- **실제 Redis 연결**: `github.com/redis/go-redis/v9` 사용
- **타임아웃 설정**: Redis 연결 타임아웃 지원
- **에러 처리**: Redis 연결 실패 시 적절한 에러 처리
- **성능 최적화**: 로컬 캐시 + Redis 조합

## 🎨 **캔버스 템플릿 구조 (업데이트)**

```
alert-threader/
├── etc-alert-threader.env.template          # 환경 파일 템플릿
├── go-advanced-redis/
│   ├── main.go                              # go-redis 실제 연결 구현
│   └── go.mod                               # go-redis/v9 의존성
├── ops-services-alert-threader-node-envfile.service  # Node.js EnvironmentFile 유닛
├── ops-services-alert-threader-go-envfile.service    # Go EnvironmentFile 유닛
├── setup-environment.sh                     # 환경 설정 스크립트
├── install-envfile-patch.sh                 # 통합 설치 스크립트
└── README-envfile-patch.md                  # 이 문서
```

## 🚀 **지원 언어 및 특징**

### **Python (FastAPI)**
- **비동기 처리**: `async/await` 지원
- **자동 문서화**: Swagger UI 제공
- **타입 힌트**: 코드 안정성 향상
- **EnvironmentFile**: 기존 방식 유지

### **Node.js (Express)**
- **가벼운 런타임**: 빠른 시작 시간
- **npm 생태계**: 풍부한 라이브러리
- **EnvironmentFile**: 환경변수 분리 적용
- **Redis 지원**: `redis` 패키지 사용

### **Go (go-redis)**
- **고성능**: 낮은 CPU/메모리 사용량
- **단일 바이너리**: 배포 간편
- **실제 Redis**: `go-redis/v9` 실제 연결
- **타임아웃 지원**: Redis 연결 타임아웃 설정

## 🛠️ **설치 방법**

### **1. 통합 설치 (권장)**

```bash
cd alert-threader
chmod +x install-envfile-patch.sh
sudo ./install-envfile-patch.sh
```

설치 과정에서 다음을 선택할 수 있습니다:
- 사용할 언어 (Python/Node.js/Go/모든 언어)
- 저장소 타입 (파일/Redis)
- Slack Bot Token
- Slack Channel ID
- 환경 설정

### **2. 환경 설정만**

```bash
cd alert-threader
chmod +x setup-environment.sh
sudo ./setup-environment.sh
```

### **3. 수동 설치**

#### **환경 파일 생성**
```bash
# 템플릿 복사
sudo cp etc-alert-threader.env.template /etc/alert-threader.env

# 권한 설정
sudo chown root:root /etc/alert-threader.env
sudo chmod 0640 /etc/alert-threader.env

# 환경 변수 수정
sudo nano /etc/alert-threader.env
```

#### **Node.js 서비스**
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

#### **Go 서비스 (go-redis)**
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

## ⚙️ **환경 설정**

### **환경 파일 구조**

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

### **보안 설정**

```bash
# 환경 파일 권한 확인
ls -la /etc/alert-threader.env
# -rw-r----- 1 root root 1234 Jan 15 10:00 /etc/alert-threader.env

# 저장소 디렉터리 권한 확인
ls -la /var/lib/alert-threader/
# drwxr-xr-x 2 www-data www-data 4096 Jan 15 10:00 .
```

## 🧪 **테스트**

### **통합 테스트**
```bash
chmod +x test-all-advanced.sh
./test-all-advanced.sh
```

### **개별 서비스 테스트**
```bash
# Node.js
curl http://localhost:9009/health | jq .
curl http://localhost:9009/stats | jq .

# Go (go-redis)
curl http://localhost:9009/health | jq .
curl http://localhost:9009/stats | jq .
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

## 🔧 **언어별 특징**

### **Node.js (EnvironmentFile)**
- **환경변수**: `/etc/alert-threader.env`에서 로드
- **Redis 연결**: `redis` 패키지 사용
- **에러 처리**: Redis 연결 실패 시 graceful degradation
- **로깅**: 환경변수 기반 로그 레벨 설정

### **Go (go-redis)**
- **실제 Redis**: `github.com/redis/go-redis/v9` 사용
- **타임아웃**: Redis 연결 타임아웃 설정
- **컨텍스트**: `context.Background()` 사용
- **에러 처리**: Redis Nil 에러 적절히 처리

## 🚨 **문제 해결**

### **1. 환경 파일 문제**
```bash
# 환경 파일 권한 확인
ls -la /etc/alert-threader.env

# 환경 파일 내용 확인
sudo cat /etc/alert-threader.env

# 환경 변수 로드 테스트
sudo systemctl show alert-threader-node --property=Environment
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
sudo journalctl -u alert-threader-node -f
sudo journalctl -u alert-threader-go -f

# 환경 변수 확인
sudo systemctl show alert-threader-node --property=Environment

# 의존성 확인
# Node.js: node -e "console.log('Node.js OK')"
# Go: go version
```

### **4. Go 빌드 실패**
```bash
# Go 모듈 확인
cd /opt/alert-threader-go-redis
go mod tidy
go mod download

# 의존성 확인
go list -m all

# 빌드 테스트
go build -o threader .
```

## 📈 **성능 비교**

| 언어 | 메모리 사용량 | CPU 사용량 | 시작 시간 | Redis 연결 | 특징 |
|------|---------------|------------|-----------|------------|------|
| **Python** | 중간 | 중간 | 느림 | redis-py | 비동기, 타입 힌트 |
| **Node.js** | 낮음 | 낮음 | 빠름 | redis | 이벤트 기반, EnvironmentFile |
| **Go** | 매우 낮음 | 매우 낮음 | 매우 빠름 | go-redis/v9 | 단일 바이너리, 실제 Redis |

## 🔄 **언어 전환**

### **서비스 중지**
```bash
# 현재 실행 중인 서비스 중지
sudo systemctl stop alert-threader-<current-language>
```

### **서비스 시작**
```bash
# 다른 언어 서비스 시작
sudo systemctl start alert-threader-<new-language>
```

### **서비스 상태 확인**
```bash
# 모든 언어 서비스 상태 확인
for lang in python nodejs go; do
    echo "=== $lang ==="
    sudo systemctl status alert-threader-$lang --no-pager
done
```

## 🔄 **업그레이드**

### **환경 파일 업데이트**
```bash
# 환경 파일 백업
sudo cp /etc/alert-threader.env /etc/alert-threader.env.bak

# 환경 파일 수정
sudo nano /etc/alert-threader.env

# 서비스 재시작
sudo systemctl restart alert-threader-<language>
```

### **코드 업데이트**
```bash
# 새 버전 복사
sudo cp -r alert-threader/*-advanced/* /opt/alert-threader/*-advanced/
sudo cp -r alert-threader/go-advanced-redis/* /opt/alert-threader/go-advanced-redis/

# 의존성 업데이트
# Node.js: cd /opt/alert-threader/nodejs-advanced && sudo npm update
# Go: cd /opt/alert-threader/go-advanced-redis && go mod tidy

# 서비스 재시작
sudo systemctl restart alert-threader-<language>
```

## 🗑️ **제거**

### **개별 언어 제거**
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

## 📄 **라이선스**

MIT License

---

## 🎯 **주요 개선사항 요약**

1. **✅ EnvironmentFile 분리**: 민감한 환경변수를 별도 파일로 분리
2. **✅ Go go-redis 실제 연결**: `go-redis/v9`를 사용한 실제 Redis 연결
3. **✅ 보안 강화**: 환경 파일 권한 관리 (640, root 소유)
4. **✅ 중앙 관리**: 모든 서비스가 동일한 환경 파일 사용
5. **✅ 타임아웃 지원**: Redis 연결 타임아웃 설정
6. **✅ 에러 처리**: Redis 연결 실패 시 적절한 에러 처리
7. **✅ 성능 최적화**: 로컬 캐시 + Redis 조합
8. **✅ 통합 설치**: 원클릭 설치 및 설정
9. **✅ 포괄적인 문서화**: 설치부터 문제해결까지 완전한 가이드

이제 **엔터프라이즈급 보안과 성능**을 갖춘 Alert Threader가 완성되었습니다! 🎉

