#!/usr/bin/env bash
set -euo pipefail

echo "🔐 DreamSeed Alert Threader 환경 설정 시작"

# 1. 환경 파일 생성
echo "📝 환경 파일 생성 중..."
sudo tee /etc/alert-threader.env >/dev/null <<'ENV'
# =============================
# Alert Threader Environment
# =============================

# =============================
# Slack Bot Configuration
# =============================
SLACK_BOT_TOKEN=xoxb-REPLACE_ME_WITH_ACTUAL_TOKEN
SLACK_CHANNEL=C0123456789     # 권장: channel ID (C로 시작)
ENVIRONMENT=staging           # staging | production

# =============================
# Storage Configuration
# =============================
# 저장소 타입: file | redis
THREAD_STORE=file

# 파일 저장소 설정 (THREAD_STORE=file일 때)
THREAD_STORE_FILE=/var/lib/alert-threader/threads.json

# Redis 저장소 설정 (THREAD_STORE=redis일 때)
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
# Redis 연결 타임아웃 (초)
REDIS_TIMEOUT=5

# 로그 레벨: debug | info | warn | error
LOG_LEVEL=info

# 최대 동시 처리 수
MAX_CONCURRENT_ALERTS=100

# =============================
# Monitoring & Health
# =============================
# 헬스체크 간격 (초)
HEALTH_CHECK_INTERVAL=30

# 통계 수집 여부
ENABLE_STATS=true

# =============================
# Advanced Configuration
# =============================
# 스레드 키 생성 전략: simple | detailed
THREAD_KEY_STRATEGY=simple

# 캐시 TTL (초, Redis만 해당)
CACHE_TTL=86400

# 재시도 설정
MAX_RETRIES=3
RETRY_DELAY=1000
ENV

# 2. 권한 설정
echo "🔒 권한 설정 중..."
sudo chown root:root /etc/alert-threader.env
sudo chmod 0640 /etc/alert-threader.env

# 3. 저장소 디렉터리 생성
echo "📁 저장소 디렉터리 생성 중..."
sudo mkdir -p /var/lib/alert-threader
sudo chown -R www-data:www-data /var/lib/alert-threader
sudo chmod 755 /var/lib/alert-threader

# 4. 환경 변수 검증
echo "✅ 환경 변수 검증 중..."
if [ -f /etc/alert-threader.env ]; then
    echo "✅ 환경 파일 생성 완료: /etc/alert-threader.env"
    echo "📋 환경 파일 내용 미리보기:"
    echo "----------------------------------------"
    head -n 20 /etc/alert-threader.env
    echo "----------------------------------------"
    echo ""
    echo "⚠️  중요: 다음 값들을 실제 값으로 수정하세요:"
    echo "   - SLACK_BOT_TOKEN=xoxb-REPLACE_ME_WITH_ACTUAL_TOKEN"
    echo "   - SLACK_CHANNEL=C0123456789"
    echo "   - ENVIRONMENT=staging"
    echo ""
    echo "🔧 수정 방법:"
    echo "   sudo nano /etc/alert-threader.env"
    echo ""
else
    echo "❌ 환경 파일 생성 실패"
    exit 1
fi

# 5. Redis 설치 (선택사항)
echo "📋 Redis 저장소를 사용하시겠습니까? (y/N)"
read -p "선택: " use_redis

if [[ $use_redis =~ ^[Yy]$ ]]; then
    echo "📦 Redis 설치 중..."
    sudo apt update
    sudo apt install -y redis-server
    
    echo "🔄 Redis 서비스 시작 중..."
    sudo systemctl enable redis-server
    sudo systemctl start redis-server
    
    # Redis 연결 테스트
    if redis-cli ping | grep -q "PONG"; then
        echo "✅ Redis: 정상 실행 중"
        
        # Redis 사용하도록 환경 파일 업데이트
        echo "🔧 환경 파일을 Redis 사용으로 업데이트 중..."
        sudo sed -i 's/THREAD_STORE=file/THREAD_STORE=redis/' /etc/alert-threader.env
        echo "✅ THREAD_STORE=redis로 변경됨"
    else
        echo "❌ Redis: 시작 실패"
        echo "   수동으로 Redis를 설치하고 다시 시도하세요:"
        echo "   sudo apt install redis-server"
        echo "   sudo systemctl start redis-server"
    fi
else
    echo "ℹ️  파일 저장소 사용 (기본값)"
fi

echo ""
echo "🎉 환경 설정 완료!"
echo ""
echo "📋 다음 단계:"
echo "1. 환경 파일 수정:"
echo "   sudo nano /etc/alert-threader.env"
echo ""
echo "2. 서비스 설치:"
echo "   # Node.js"
echo "   sudo cp ops-services-alert-threader-node-envfile.service /etc/systemd/system/alert-threader-node.service"
echo "   sudo systemctl daemon-reload"
echo "   sudo systemctl enable --now alert-threader-node"
echo ""
echo "   # Go (go-redis)"
echo "   sudo cp ops-services-alert-threader-go-envfile.service /etc/systemd/system/alert-threader-go.service"
echo "   sudo systemctl daemon-reload"
echo "   sudo systemctl enable --now alert-threader-go"
echo ""
echo "3. 서비스 상태 확인:"
echo "   sudo systemctl status alert-threader-node"
echo "   sudo systemctl status alert-threader-go"
echo ""
echo "4. 로그 확인:"
echo "   sudo journalctl -u alert-threader-node -f"
echo "   sudo journalctl -u alert-threader-go -f"

