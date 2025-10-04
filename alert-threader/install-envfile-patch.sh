#!/usr/bin/env bash
set -euo pipefail

echo "🔐 DreamSeed Alert Threader EnvironmentFile + go-redis 패치 설치 시작"

# 1. 언어 선택
echo "📋 사용할 언어를 선택하세요:"
echo "  1) Python (FastAPI) - 기존"
echo "  2) Node.js (Express) - EnvironmentFile"
echo "  3) Go (go-redis) - EnvironmentFile + 실제 Redis 연결"
echo "  4) 모든 언어 설치"
read -p "선택 (1-4): " choice

case $choice in
    1)
        LANGUAGES=("python")
        ;;
    2)
        LANGUAGES=("nodejs")
        ;;
    3)
        LANGUAGES=("go")
        ;;
    4)
        LANGUAGES=("python" "nodejs" "go")
        ;;
    *)
        echo "❌ 잘못된 선택입니다"
        exit 1
        ;;
esac

# 2. 저장소 선택
echo "📋 저장소를 선택하세요:"
echo "  1) 파일 저장소 (기본값, 단순함)"
echo "  2) Redis 저장소 (고성능, 확장성)"
read -p "선택 (1-2): " store_choice

case $store_choice in
    1)
        THREAD_STORE="file"
        THREAD_STORE_FILE="/var/lib/alert-threader/threads.json"
        echo "✅ 선택된 저장소: 파일 ($THREAD_STORE_FILE)"
        ;;
    2)
        THREAD_STORE="redis"
        REDIS_URL="redis://localhost:6379/0"
        REDIS_KEY_PREFIX="threader:ts"
        echo "✅ 선택된 저장소: Redis ($REDIS_URL)"
        ;;
    *)
        echo "❌ 잘못된 선택입니다"
        exit 1
        ;;
esac

# 3. 필수 패키지 설치
echo "📦 필수 패키지 설치 중..."
sudo apt update
sudo apt install -y curl jq nginx certbot python3-certbot-nginx

# 언어별 패키지 설치
for lang in "${LANGUAGES[@]}"; do
    case $lang in
        python)
            echo "📦 Python 패키지 설치 중..."
            sudo apt install -y python3 python3-pip python3-venv
            ;;
        nodejs)
            echo "📦 Node.js 패키지 설치 중..."
            curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
            sudo apt install -y nodejs
            ;;
        go)
            echo "📦 Go 패키지 설치 중..."
            sudo apt install -y golang-go
            ;;
    esac
done

# Redis 선택 시 Redis 설치
if [ "$THREAD_STORE" = "redis" ]; then
    echo "📦 Redis 설치 중..."
    sudo apt install -y redis-server
    sudo systemctl enable redis-server
    sudo systemctl start redis-server
    
    # Redis 연결 테스트
    if redis-cli ping | grep -q "PONG"; then
        echo "✅ Redis: 정상 실행 중"
    else
        echo "❌ Redis: 시작 실패"
        exit 1
    fi
fi

# 4. 환경 파일 설정
echo "🔐 환경 파일 설정 중..."
sudo tee /etc/alert-threader.env >/dev/null <<ENV
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
THREAD_STORE=$THREAD_STORE

# 파일 저장소 설정 (THREAD_STORE=file일 때)
THREAD_STORE_FILE=$THREAD_STORE_FILE

# Redis 저장소 설정 (THREAD_STORE=redis일 때)
REDIS_URL=$REDIS_URL
REDIS_KEY_PREFIX=$REDIS_KEY_PREFIX

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

# 권한 설정
sudo chown root:root /etc/alert-threader.env
sudo chmod 0640 /etc/alert-threader.env

# 5. 캔버스 구조 생성
echo "📁 캔버스 구조 생성 중..."
sudo mkdir -p /opt/alert-threader
sudo mkdir -p /var/lib/alert-threader
sudo mkdir -p /etc/nginx/sites-available
sudo mkdir -p /etc/nginx/sites-enabled
sudo chown -R www-data:www-data /opt/alert-threader
sudo chown -R www-data:www-data /var/lib/alert-threader

# 6. 파일 복사 (캔버스 구조)
echo "📋 파일 복사 중..."
for lang in "${LANGUAGES[@]}"; do
    case $lang in
        python)
            echo "  - Python 고급 버전 복사 중..."
            sudo cp -r python-advanced/* /opt/alert-threader/python-advanced/
            sudo chown -R www-data:www-data /opt/alert-threader/python-advanced
            ;;
        nodejs)
            echo "  - Node.js 고급 버전 복사 중..."
            sudo cp -r nodejs-advanced/* /opt/alert-threader/nodejs-advanced/
            sudo chown -R www-data:www-data /opt/alert-threader/nodejs-advanced
            ;;
        go)
            echo "  - Go go-redis 버전 복사 중..."
            sudo cp -r go-advanced-redis/* /opt/alert-threader/go-advanced-redis/
            sudo chown -R www-data:www-data /opt/alert-threader/go-advanced-redis
            ;;
    esac
done

# 7. systemd 서비스 설정 (EnvironmentFile 사용)
echo "⚙️ systemd 서비스 설정 중..."
for lang in "${LANGUAGES[@]}"; do
    case $lang in
        python)
            SERVICE_FILE="alert-threader-advanced.service"
            TARGET_NAME="alert-threader-python"
            ;;
        nodejs)
            SERVICE_FILE="ops-services-alert-threader-node-envfile.service"
            TARGET_NAME="alert-threader-node"
            ;;
        go)
            SERVICE_FILE="ops-services-alert-threader-go-envfile.service"
            TARGET_NAME="alert-threader-go"
            ;;
    esac
    
    echo "  - $lang 서비스 설정 중..."
    sudo cp "$SERVICE_FILE" /etc/systemd/system/$TARGET_NAME.service
    sudo chown root:root /etc/systemd/system/$TARGET_NAME.service
    sudo chmod 644 /etc/systemd/system/$TARGET_NAME.service
done

# 8. Nginx 템플릿 설정
echo "🌐 Nginx 템플릿 설정 중..."
sudo cp ops-nginx-dreamseed.conf.tpl /etc/nginx/sites-available/dreamseed.conf.tpl
sudo chown root:root /etc/nginx/sites-available/dreamseed.conf.tpl
sudo chmod 644 /etc/nginx/sites-available/dreamseed.conf.tpl

# 9. 스크립트 설치
echo "🔧 스크립트 설치 중..."
sudo cp ops-scripts-*.sh /usr/local/bin/
sudo chmod +x /usr/local/bin/ops-scripts-*.sh

# 10. 환경 변수 입력
echo "🔧 환경 변수 입력 중..."
read -p "Slack Bot Token (xoxb-...): " SLACK_BOT_TOKEN
read -p "Slack Channel ID (C0123456789): " SLACK_CHANNEL
read -p "Environment (staging/production): " ENVIRONMENT

# 환경 변수 업데이트
sudo sed -i "s/SLACK_BOT_TOKEN=xoxb-REPLACE_ME_WITH_ACTUAL_TOKEN/SLACK_BOT_TOKEN=$SLACK_BOT_TOKEN/" /etc/alert-threader.env
sudo sed -i "s/SLACK_CHANNEL=C0123456789/SLACK_CHANNEL=$SLACK_CHANNEL/" /etc/alert-threader.env
sudo sed -i "s/ENVIRONMENT=staging/ENVIRONMENT=$ENVIRONMENT/" /etc/alert-threader.env

# 11. systemd 데몬 리로드
echo "🔄 systemd 데몬 리로드 중..."
sudo systemctl daemon-reload

# 12. 서비스 시작 (첫 번째 언어만)
FIRST_LANG="${LANGUAGES[0]}"
case $FIRST_LANG in
    python)
        SERVICE_NAME="alert-threader-python"
        ;;
    nodejs)
        SERVICE_NAME="alert-threader-node"
        ;;
    go)
        SERVICE_NAME="alert-threader-go"
        ;;
esac

echo "▶️ $SERVICE_NAME 서비스 시작 중..."
sudo systemctl enable $SERVICE_NAME
sudo systemctl start $SERVICE_NAME

# 13. 상태 확인
echo "📊 서비스 상태 확인 중..."
sleep 5
if systemctl is-active --quiet $SERVICE_NAME; then
    echo "✅ Alert Threader ($SERVICE_NAME): 정상 실행 중"
else
    echo "❌ Alert Threader ($SERVICE_NAME): 시작 실패"
    echo "로그 확인: sudo journalctl -u $SERVICE_NAME -f"
    exit 1
fi

# 14. 포트 확인
echo "🔍 포트 확인 중..."
if netstat -tlnp | grep -q ":9009 "; then
    echo "✅ 포트 9009: 열림"
else
    echo "❌ 포트 9009: 닫힘"
fi

# 15. 헬스체크
echo "🏥 헬스체크 중..."
sleep 2
if curl -s http://localhost:9009/health | jq .; then
    echo "✅ 헬스체크: 성공"
else
    echo "❌ 헬스체크: 실패"
fi

# 16. 통계 확인
echo "📊 통계 확인 중..."
if curl -s http://localhost:9009/stats | jq .; then
    echo "✅ 통계 조회: 성공"
else
    echo "❌ 통계 조회: 실패"
fi

echo "🎉 DreamSeed Alert Threader EnvironmentFile + go-redis 패치 설치 완료!"
echo ""
echo "📋 설정 요약:"
echo "  - 설치된 언어: ${LANGUAGES[*]}"
echo "  - 저장소: $THREAD_STORE"
if [ "$THREAD_STORE" = "file" ]; then
    echo "  - 파일 경로: $THREAD_STORE_FILE"
else
    echo "  - Redis URL: $REDIS_URL"
    echo "  - Redis 키 접두사: $REDIS_KEY_PREFIX"
fi
echo "  - 서비스: $SERVICE_NAME"
echo "  - 포트: 9009"
echo "  - 채널: $SLACK_CHANNEL"
echo "  - 환경: $ENVIRONMENT"
echo "  - 환경 파일: /etc/alert-threader.env"
echo ""
echo "🔧 다음 단계:"
echo "  1. Nginx 설정:"
echo "     sudo ops-scripts-deploy_proxy_and_tls.sh dreamseedai.com /var/www/dreamseed/static http://127.0.0.1:8000/ on"
echo ""
echo "  2. 다른 언어 서비스 시작 (선택사항):"
for lang in "${LANGUAGES[@]}"; do
    if [ "$lang" != "$FIRST_LANG" ]; then
        case $lang in
            python)
                echo "     sudo systemctl start alert-threader-python"
                ;;
            nodejs)
                echo "     sudo systemctl start alert-threader-node"
                ;;
            go)
                echo "     sudo systemctl start alert-threader-go"
                ;;
        esac
    fi
done
echo ""
echo "  3. 테스트 실행:"
echo "     chmod +x test-all-advanced.sh"
echo "     ./test-all-advanced.sh"
echo ""
echo "  4. 로그 확인:"
echo "     sudo journalctl -u $SERVICE_NAME -f"
echo ""
echo "  5. 통계 모니터링:"
echo "     curl http://localhost:9009/stats | jq ."
echo ""
echo "  6. 환경 파일 수정 (필요시):"
echo "     sudo nano /etc/alert-threader.env"

