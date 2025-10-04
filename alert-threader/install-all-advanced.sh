#!/usr/bin/env bash
set -euo pipefail

echo "🚀 DreamSeed Alert Threader - All Languages Advanced 설치 시작"

# 1. 언어 선택
echo "📋 사용할 언어를 선택하세요:"
echo "  1) Python (FastAPI) - 권장"
echo "  2) Node.js (Express)"
echo "  3) Go"
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
sudo apt install -y curl jq

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

# 4. 디렉터리 생성
echo "📁 디렉터리 생성 중..."
sudo mkdir -p /opt/alert-threader
sudo mkdir -p /var/lib/alert-threader
sudo chown -R www-data:www-data /opt/alert-threader
sudo chown -R www-data:www-data /var/lib/alert-threader

# 5. 파일 복사
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
            echo "  - Go 고급 버전 복사 중..."
            sudo cp -r go-advanced/* /opt/alert-threader/go-advanced/
            sudo chown -R www-data:www-data /opt/alert-threader/go-advanced
            ;;
    esac
done

# 6. 환경 변수 설정
echo "🔧 환경 변수 설정 중..."
read -p "Slack Bot Token (xoxb-...): " SLACK_BOT_TOKEN
read -p "Slack Channel ID (C0123456789): " SLACK_CHANNEL
read -p "Environment (staging/production): " ENVIRONMENT

# 7. systemd 서비스 설정
echo "⚙️ systemd 서비스 설정 중..."
for lang in "${LANGUAGES[@]}"; do
    case $lang in
        python)
            SERVICE_FILE="alert-threader-advanced.service"
            ;;
        nodejs)
            SERVICE_FILE="alert-threader-nodejs-advanced.service"
            ;;
        go)
            SERVICE_FILE="alert-threader-go-advanced.service"
            ;;
    esac
    
    echo "  - $lang 서비스 설정 중..."
    sudo cp systemd/$SERVICE_FILE /etc/systemd/system/alert-threader-$lang.service
    sudo chown root:root /etc/systemd/system/alert-threader-$lang.service
    sudo chmod 644 /etc/systemd/system/alert-threader-$lang.service
done

# 8. 환경 변수 override 설정
echo "🔧 환경 변수 override 설정 중..."
for lang in "${LANGUAGES[@]}"; do
    sudo mkdir -p /etc/systemd/system/alert-threader-$lang.service.d
    cat << EOF | sudo tee /etc/systemd/system/alert-threader-$lang.service.d/override.conf
[Service]
Environment=SLACK_BOT_TOKEN=$SLACK_BOT_TOKEN
Environment=SLACK_CHANNEL=$SLACK_CHANNEL
Environment=ENVIRONMENT=$ENVIRONMENT
Environment=THREAD_STORE=$THREAD_STORE
EOF

    # 저장소별 환경 변수 추가
    if [ "$THREAD_STORE" = "file" ]; then
        echo "Environment=THREAD_STORE_FILE=$THREAD_STORE_FILE" | sudo tee -a /etc/systemd/system/alert-threader-$lang.service.d/override.conf
    else
        echo "Environment=REDIS_URL=$REDIS_URL" | sudo tee -a /etc/systemd/system/alert-threader-$lang.service.d/override.conf
        echo "Environment=REDIS_KEY_PREFIX=$REDIS_KEY_PREFIX" | sudo tee -a /etc/systemd/system/alert-threader-$lang.service.d/override.conf
    fi
done

# 9. systemd 데몬 리로드
echo "🔄 systemd 데몬 리로드 중..."
sudo systemctl daemon-reload

# 10. 서비스 시작 (첫 번째 언어만)
FIRST_LANG="${LANGUAGES[0]}"
echo "▶️ $FIRST_LANG 서비스 시작 중..."
sudo systemctl enable alert-threader-$FIRST_LANG
sudo systemctl start alert-threader-$FIRST_LANG

# 11. 상태 확인
echo "📊 서비스 상태 확인 중..."
sleep 5
if systemctl is-active --quiet alert-threader-$FIRST_LANG; then
    echo "✅ Alert Threader ($FIRST_LANG): 정상 실행 중"
else
    echo "❌ Alert Threader ($FIRST_LANG): 시작 실패"
    echo "로그 확인: sudo journalctl -u alert-threader-$FIRST_LANG -f"
    exit 1
fi

# 12. 포트 확인
echo "🔍 포트 확인 중..."
if netstat -tlnp | grep -q ":9009 "; then
    echo "✅ 포트 9009: 열림"
else
    echo "❌ 포트 9009: 닫힘"
fi

# 13. 헬스체크
echo "🏥 헬스체크 중..."
sleep 2
if curl -s http://localhost:9009/health | jq .; then
    echo "✅ 헬스체크: 성공"
else
    echo "❌ 헬스체크: 실패"
fi

# 14. 통계 확인
echo "📊 통계 확인 중..."
if curl -s http://localhost:9009/stats | jq .; then
    echo "✅ 통계 조회: 성공"
else
    echo "❌ 통계 조회: 실패"
fi

echo "🎉 DreamSeed Alert Threader - All Languages Advanced 설치 완료!"
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
echo "  - 서비스: alert-threader-*"
echo "  - 포트: 9009"
echo "  - 채널: $SLACK_CHANNEL"
echo "  - 환경: $ENVIRONMENT"
echo ""
echo "🔧 다음 단계:"
echo "  1. Alertmanager 설정 업데이트:"
echo "     sudo cp alertmanager-threader.yml /etc/alertmanager/alertmanager.yml"
echo "     sudo systemctl restart alertmanager"
echo ""
echo "  2. 다른 언어 서비스 시작 (선택사항):"
for lang in "${LANGUAGES[@]}"; do
    if [ "$lang" != "$FIRST_LANG" ]; then
        echo "     sudo systemctl start alert-threader-$lang"
    fi
done
echo ""
echo "  3. 테스트 실행:"
echo "     chmod +x test-advanced.sh"
echo "     ./test-advanced.sh"
echo ""
echo "  4. 로그 확인:"
for lang in "${LANGUAGES[@]}"; do
    echo "     sudo journalctl -u alert-threader-$lang -f"
done
echo ""
echo "  5. 통계 모니터링:"
echo "     curl http://localhost:9009/stats | jq ."

