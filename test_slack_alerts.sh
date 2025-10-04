#!/usr/bin/env bash
set -euo pipefail

echo "🧪 DreamSeed Slack 알림 테스트 시작"

# 1. Alertmanager 상태 확인
echo "📊 Alertmanager 상태 확인 중..."
if systemctl is-active --quiet alertmanager; then
    echo "✅ Alertmanager: 실행 중"
else
    echo "❌ Alertmanager: 중지됨"
    exit 1
fi

# 2. 설정 검증
echo "⚙️ Alertmanager 설정 검증 중..."
if command -v amtool >/dev/null 2>&1; then
    if sudo amtool check-config /etc/alertmanager/alertmanager.yml; then
        echo "✅ Alertmanager 설정: 유효"
    else
        echo "❌ Alertmanager 설정: 오류"
        exit 1
    fi
else
    echo "⚠️ amtool이 설치되지 않음"
fi

# 3. 템플릿 파일 확인
echo "📝 템플릿 파일 확인 중..."
if [ -f "/etc/alertmanager/templates/slack.tmpl" ]; then
    echo "✅ Slack 템플릿: 존재"
else
    echo "❌ Slack 템플릿: 없음"
    echo "템플릿 파일을 복사하세요:"
    echo "sudo cp monitoring/alertmanager/templates/slack.tmpl /etc/alertmanager/templates/"
    exit 1
fi

# 4. 테스트 알림 전송
echo "📨 테스트 알림 전송 중..."

# Critical 알림 테스트
echo "🚨 Critical 알림 테스트..."
sudo amtool --alertmanager.url=http://localhost:9093 alert add \
    -l alertname=DreamSeedTestCritical -l severity=critical -l service=test \
    -a summary="DreamSeed Critical 테스트 알림" \
    -a description="이것은 Critical 심각도의 테스트 알림입니다. 즉시 확인이 필요합니다." \
    2>/dev/null || echo "Critical 알림 전송 실패"

sleep 2

# Warning 알림 테스트
echo "⚠️ Warning 알림 테스트..."
sudo amtool --alertmanager.url=http://localhost:9093 alert add \
    -l alertname=DreamSeedTestWarning -l severity=warning -l service=test \
    -a summary="DreamSeed Warning 테스트 알림" \
    -a description="이것은 Warning 심각도의 테스트 알림입니다. 조사가 필요합니다." \
    2>/dev/null || echo "Warning 알림 전송 실패"

sleep 2

# Info 알림 테스트
echo "ℹ️ Info 알림 테스트..."
sudo amtool --alertmanager.url=http://localhost:9093 alert add \
    -l alertname=DreamSeedTestInfo -l severity=info -l service=test \
    -a summary="DreamSeed Info 테스트 알림" \
    -a description="이것은 Info 심각도의 테스트 알림입니다. 참고용입니다." \
    2>/dev/null || echo "Info 알림 전송 실패"

sleep 2

# Backup 알림 테스트
echo "💾 Backup 알림 테스트..."
sudo amtool --alertmanager.url=http://localhost:9093 alert add \
    -l alertname=DreamSeedTestBackup -l severity=warning -l service=backup \
    -a summary="DreamSeed Backup 테스트 알림" \
    -a description="이것은 백업 서비스의 테스트 알림입니다." \
    2>/dev/null || echo "Backup 알림 전송 실패"

sleep 2

# 5. 현재 알림 목록 확인
echo "📋 현재 알림 목록:"
sudo amtool --alertmanager.url=http://localhost:9093 alert query 2>/dev/null || echo "알림을 가져올 수 없습니다"

# 6. 알림 해제 테스트
echo "✅ 알림 해제 테스트..."
sudo amtool --alertmanager.url=http://localhost:9093 alert add \
    -l alertname=DreamSeedTestResolved -l severity=info -l service=test \
    -a summary="DreamSeed 해제 테스트 알림" \
    -a description="이 알림은 곧 해제될 예정입니다." \
    2>/dev/null || echo "해제 테스트 알림 전송 실패"

sleep 5

# 알림 해제
sudo amtool --alertmanager.url=http://localhost:9093 alert add \
    -l alertname=DreamSeedTestResolved -l severity=info -l service=test \
    -a summary="DreamSeed 해제 테스트 알림" \
    -a description="이 알림은 해제되었습니다." \
    --expires=1s 2>/dev/null || echo "알림 해제 실패"

# 7. 로그 확인
echo "📝 최근 Alertmanager 로그 확인 중..."
echo "--- Alertmanager 로그 (최근 10줄) ---"
sudo journalctl -u alertmanager --no-pager -n 10 || echo "로그를 가져올 수 없습니다"

# 8. Slack Webhook URL 확인
echo "🔗 Slack Webhook URL 확인 중..."
if grep -q "T00000000" /etc/systemd/system/alertmanager.service.d/override.conf; then
    echo "⚠️ Slack Webhook URL이 기본값입니다. 실제 URL로 변경하세요:"
    echo "sudo nano /etc/systemd/system/alertmanager.service.d/override.conf"
else
    echo "✅ Slack Webhook URL이 설정되어 있습니다"
fi

# 9. 채널 설정 확인
echo "📢 Slack 채널 설정 확인 중..."
channels=("SLACK_CHANNEL_CRITICAL" "SLACK_CHANNEL_WARNING" "SLACK_CHANNEL_INFO" "SLACK_CHANNEL_BACKUP")
for channel in "${channels[@]}"; do
    if grep -q "$channel" /etc/systemd/system/alertmanager.service.d/override.conf; then
        echo "✅ $channel: 설정됨"
    else
        echo "⚠️ $channel: 기본값 사용"
    fi
done

echo "🎉 Slack 알림 테스트 완료!"
echo ""
echo "📋 다음 단계:"
echo "  1. Slack 워크스페이스에서 채널 생성:"
echo "     - #dreamseed-critical"
echo "     - #dreamseed-warnings" 
echo "     - #dreamseed-info"
echo "     - #dreamseed-backup"
echo ""
echo "  2. Slack Webhook URL 설정:"
echo "     sudo nano /etc/systemd/system/alertmanager.service.d/override.conf"
echo ""
echo "  3. Alertmanager 재시작:"
echo "     sudo systemctl daemon-reload"
echo "     sudo systemctl restart alertmanager"
echo ""
echo "  4. 실제 알림 테스트:"
echo "     ./test_slack_alerts.sh"

