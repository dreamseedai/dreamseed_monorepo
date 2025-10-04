#!/usr/bin/env bash
set -euo pipefail

echo "🚀 DreamSeed Alert Threader - Advanced 설치 시작"

# 1. 저장소 선택
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

# 2. 필수 패키지 설치
echo "📦 필수 패키지 설치 중..."
sudo apt update
sudo apt install -y python3 python3-pip python3-venv curl jq

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

# 3. 디렉터리 생성
echo "📁 디렉터리 생성 중..."
sudo mkdir -p /opt/alert-threader/python-advanced
sudo mkdir -p /var/lib/alert-threader
sudo chown -R www-data:www-data /opt/alert-threader
sudo chown -R www-data:www-data /var/lib/alert-threader

# 4. 파일 복사
echo "📋 파일 복사 중..."
sudo cp -r python-advanced/* /opt/alert-threader/python-advanced/
sudo chown -R www-data:www-data /opt/alert-threader/python-advanced

# 5. systemd 서비스 설정
echo "⚙️ systemd 서비스 설정 중..."
sudo cp systemd/alert-threader-advanced.service /etc/systemd/system/alert-threader.service
sudo chown root:root /etc/systemd/system/alert-threader.service
sudo chmod 644 /etc/systemd/system/alert-threader.service

# 6. 환경 변수 설정
echo "🔧 환경 변수 설정 중..."
read -p "Slack Bot Token (xoxb-...): " SLACK_BOT_TOKEN
read -p "Slack Channel ID (C0123456789): " SLACK_CHANNEL
read -p "Environment (staging/production): " ENVIRONMENT

# systemd override 생성
sudo mkdir -p /etc/systemd/system/alert-threader.service.d
cat << EOF | sudo tee /etc/systemd/system/alert-threader.service.d/override.conf
[Service]
Environment=SLACK_BOT_TOKEN=$SLACK_BOT_TOKEN
Environment=SLACK_CHANNEL=$SLACK_CHANNEL
Environment=ENVIRONMENT=$ENVIRONMENT
Environment=THREAD_STORE=$THREAD_STORE
EOF

# 저장소별 환경 변수 추가
if [ "$THREAD_STORE" = "file" ]; then
    echo "Environment=THREAD_STORE_FILE=$THREAD_STORE_FILE" | sudo tee -a /etc/systemd/system/alert-threader.service.d/override.conf
else
    echo "Environment=REDIS_URL=$REDIS_URL" | sudo tee -a /etc/systemd/system/alert-threader.service.d/override.conf
    echo "Environment=REDIS_KEY_PREFIX=$REDIS_KEY_PREFIX" | sudo tee -a /etc/systemd/system/alert-threader.service.d/override.conf
fi

# 7. systemd 데몬 리로드
echo "🔄 systemd 데몬 리로드 중..."
sudo systemctl daemon-reload

# 8. 서비스 시작
echo "▶️ 서비스 시작 중..."
sudo systemctl enable alert-threader
sudo systemctl start alert-threader

# 9. 상태 확인
echo "📊 서비스 상태 확인 중..."
sleep 5
if systemctl is-active --quiet alert-threader; then
    echo "✅ Alert Threader: 정상 실행 중"
else
    echo "❌ Alert Threader: 시작 실패"
    echo "로그 확인: sudo journalctl -u alert-threader -f"
    exit 1
fi

# 10. 포트 확인
echo "🔍 포트 확인 중..."
if netstat -tlnp | grep -q ":9009 "; then
    echo "✅ 포트 9009: 열림"
else
    echo "❌ 포트 9009: 닫힘"
fi

# 11. 헬스체크
echo "🏥 헬스체크 중..."
sleep 2
if curl -s http://localhost:9009/health | jq .; then
    echo "✅ 헬스체크: 성공"
else
    echo "❌ 헬스체크: 실패"
fi

# 12. 통계 확인
echo "📊 통계 확인 중..."
if curl -s http://localhost:9009/stats | jq .; then
    echo "✅ 통계 조회: 성공"
else
    echo "❌ 통계 조회: 실패"
fi

echo "🎉 DreamSeed Alert Threader - Advanced 설치 완료!"
echo ""
echo "📋 설정 요약:"
echo "  - 저장소: $THREAD_STORE"
if [ "$THREAD_STORE" = "file" ]; then
    echo "  - 파일 경로: $THREAD_STORE_FILE"
else
    echo "  - Redis URL: $REDIS_URL"
    echo "  - Redis 키 접두사: $REDIS_KEY_PREFIX"
fi
echo "  - 서비스: alert-threader"
echo "  - 포트: 9009"
echo "  - 채널: $SLACK_CHANNEL"
echo "  - 환경: $ENVIRONMENT"
echo ""
echo "🔧 다음 단계:"
echo "  1. Alertmanager 설정 업데이트:"
echo "     sudo cp alertmanager-threader.yml /etc/alertmanager/alertmanager.yml"
echo "     sudo systemctl restart alertmanager"
echo ""
echo "  2. 테스트 실행:"
echo "     chmod +x test-advanced.sh"
echo "     ./test-advanced.sh"
echo ""
echo "  3. 로그 확인:"
echo "     sudo journalctl -u alert-threader -f"
echo ""
echo "  4. 통계 모니터링:"
echo "     curl http://localhost:9009/stats | jq ."

