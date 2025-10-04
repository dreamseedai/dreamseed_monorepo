#!/usr/bin/env bash
set -euo pipefail

echo "📢 DreamSeed Slack 설정 업데이트 시작"

# 1. 템플릿 파일 복사
echo "📝 Slack 템플릿 파일 복사 중..."
sudo mkdir -p /etc/alertmanager/templates
sudo cp monitoring/alertmanager/templates/slack.tmpl /etc/alertmanager/templates/
sudo chown alertmanager:alertmanager /etc/alertmanager/templates/slack.tmpl
sudo chmod 644 /etc/alertmanager/templates/slack.tmpl
echo "✅ Slack 템플릿 파일 복사 완료"

# 2. Alertmanager 설정 업데이트
echo "⚙️ Alertmanager 설정 업데이트 중..."
sudo cp monitoring/alertmanager/alertmanager.yml /etc/alertmanager/
sudo chown alertmanager:alertmanager /etc/alertmanager/alertmanager.yml
sudo chmod 644 /etc/alertmanager/alertmanager.yml
echo "✅ Alertmanager 설정 업데이트 완료"

# 3. systemd override 설정 업데이트
echo "🔧 systemd override 설정 업데이트 중..."
sudo mkdir -p /etc/systemd/system/alertmanager.service.d
sudo cp monitoring/alertmanager/alertmanager.service.d/override.conf /etc/systemd/system/alertmanager.service.d/
sudo chmod 644 /etc/systemd/system/alertmanager.service.d/override.conf
echo "✅ systemd override 설정 업데이트 완료"

# 4. 설정 검증
echo "✅ 설정 검증 중..."
if command -v amtool >/dev/null 2>&1; then
    if sudo amtool check-config /etc/alertmanager/alertmanager.yml; then
        echo "✅ Alertmanager 설정: 유효"
    else
        echo "❌ Alertmanager 설정: 오류"
        exit 1
    fi
else
    echo "⚠️ amtool이 설치되지 않음 - 수동으로 검증하세요"
fi

# 5. systemd 데몬 리로드
echo "🔄 systemd 데몬 리로드 중..."
sudo systemctl daemon-reload

# 6. Alertmanager 재시작
echo "▶️ Alertmanager 재시작 중..."
sudo systemctl restart alertmanager

# 7. 서비스 상태 확인
echo "📊 서비스 상태 확인 중..."
sleep 3
if systemctl is-active --quiet alertmanager; then
    echo "✅ Alertmanager: 정상 실행 중"
else
    echo "❌ Alertmanager: 시작 실패"
    echo "로그 확인: sudo journalctl -u alertmanager -f"
    exit 1
fi

# 8. 포트 확인
echo "🔍 포트 확인 중..."
if netstat -tlnp | grep -q ":9093 "; then
    echo "✅ Alertmanager 포트 9093: 열림"
else
    echo "❌ Alertmanager 포트 9093: 닫힘"
fi

echo "🎉 DreamSeed Slack 설정 업데이트 완료!"
echo ""
echo "📋 설정 요약:"
echo "  - 템플릿 파일: /etc/alertmanager/templates/slack.tmpl"
echo "  - Alertmanager 설정: /etc/alertmanager/alertmanager.yml"
echo "  - systemd override: /etc/systemd/system/alertmanager.service.d/override.conf"
echo ""
echo "🔧 다음 단계:"
echo "  1. Slack Webhook URL 설정:"
echo "     sudo nano /etc/systemd/system/alertmanager.service.d/override.conf"
echo ""
echo "  2. Slack 채널 생성 (선택사항):"
echo "     - #dreamseed-critical"
echo "     - #dreamseed-warnings"
echo "     - #dreamseed-info"
echo "     - #dreamseed-backup"
echo ""
echo "  3. 테스트 실행:"
echo "     chmod +x test_slack_alerts.sh"
echo "     ./test_slack_alerts.sh"

