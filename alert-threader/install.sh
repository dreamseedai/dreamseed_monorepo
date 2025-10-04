#!/usr/bin/env bash
set -euo pipefail

echo "🚀 DreamSeed Alert Threader 설치 시작"

# 1. 사용자 선택
echo "📋 사용할 언어를 선택하세요:"
echo "  1) Python (FastAPI) - 권장"
echo "  2) Node.js (Express)"
echo "  3) Go"
read -p "선택 (1-3): " choice

case $choice in
    1)
        LANG="python"
        SERVICE_FILE="alert-threader-python.service"
        ;;
    2)
        LANG="nodejs"
        SERVICE_FILE="alert-threader-nodejs.service"
        ;;
    3)
        LANG="go"
        SERVICE_FILE="alert-threader-go.service"
        ;;
    *)
        echo "❌ 잘못된 선택입니다"
        exit 1
        ;;
esac

echo "✅ 선택된 언어: $LANG"

# 2. 필수 패키지 설치
echo "📦 필수 패키지 설치 중..."
sudo apt update
sudo apt install -y curl jq

case $LANG in
    python)
        sudo apt install -y python3 python3-pip python3-venv
        ;;
    nodejs)
        curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
        sudo apt install -y nodejs
        ;;
    go)
        sudo apt install -y golang-go
        ;;
esac

# 3. 디렉터리 생성
echo "📁 디렉터리 생성 중..."
sudo mkdir -p /opt/alert-threader
sudo chown -R www-data:www-data /opt/alert-threader

# 4. 파일 복사
echo "📋 파일 복사 중..."
sudo cp -r alert-threader/$LANG/* /opt/alert-threader/$LANG/
sudo chown -R www-data:www-data /opt/alert-threader/$LANG

# 5. systemd 서비스 설정
echo "⚙️ systemd 서비스 설정 중..."
sudo cp systemd/$SERVICE_FILE /etc/systemd/system/alert-threader.service
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
EOF

# 7. systemd 데몬 리로드
echo "🔄 systemd 데몬 리로드 중..."
sudo systemctl daemon-reload

# 8. 서비스 시작
echo "▶️ 서비스 시작 중..."
sudo systemctl enable alert-threader
sudo systemctl start alert-threader

# 9. 상태 확인
echo "📊 서비스 상태 확인 중..."
sleep 3
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
if curl -s http://localhost:9009/health | jq .; then
    echo "✅ 헬스체크: 성공"
else
    echo "❌ 헬스체크: 실패"
fi

echo "🎉 DreamSeed Alert Threader 설치 완료!"
echo ""
echo "📋 설정 요약:"
echo "  - 언어: $LANG"
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
echo "     curl -X POST http://localhost:9009/alert \\"
echo "       -H 'Content-Type: application/json' \\"
echo "       -d '{\"status\":\"firing\",\"alerts\":[{\"labels\":{\"alertname\":\"TestAlert\",\"severity\":\"critical\"},\"annotations\":{\"summary\":\"테스트 알림\"}}]}'"
echo ""
echo "  3. 로그 확인:"
echo "     sudo journalctl -u alert-threader -f"

