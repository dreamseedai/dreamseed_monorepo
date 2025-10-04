#!/bin/bash

# ⏰ cron 설정 스크립트 (자동화 힌트)

set -e

echo "⏰ DreamSeed AI cron 자동화 설정"
echo "=================================="

# 현재 cron 작업 확인
echo "📋 현재 cron 작업:"
crontab -l 2>/dev/null || echo "cron 작업 없음"

echo ""

# 권장 cron 작업
echo "🔧 권장 cron 작업:"
echo "=================="

echo "1️⃣ 일일 리포트 (매일 오전 9시)"
echo "   0 9 * * * /home/won/projects/dreamseed_monorepo/daily-report.sh"

echo ""
echo "2️⃣ 헬스체크 (5분마다)"
echo "   */5 * * * * /home/won/projects/dreamseed_monorepo/simple-alert.sh"

echo ""
echo "3️⃣ 로그 분석 (매일 오후 6시)"
echo "   0 18 * * * /home/won/projects/dreamseed_monorepo/6line-summary.sh >> /tmp/daily-analysis.log"

echo ""
echo "4️⃣ 캐시 모니터링 (매주 월요일 오전 8시)"
echo "   0 8 * * 1 /home/won/projects/dreamseed_monorepo/cache-monitor.sh"

echo ""

# 사용자 선택
echo "🤔 어떤 cron 작업을 설정하시겠습니까?"
echo "1) 일일 리포트만"
echo "2) 헬스체크만"
echo "3) 모든 작업"
echo "4) 사용자 정의"
echo "5) 취소"

read -p "선택 (1-5): " CHOICE

case $CHOICE in
  1)
    echo "📅 일일 리포트 cron 설정 중..."
    (crontab -l 2>/dev/null; echo "0 9 * * * /home/won/projects/dreamseed_monorepo/daily-report.sh") | crontab -
    echo "✅ 일일 리포트가 매일 오전 9시에 실행됩니다"
    ;;
  2)
    echo "🔍 헬스체크 cron 설정 중..."
    (crontab -l 2>/dev/null; echo "*/5 * * * * /home/won/projects/dreamseed_monorepo/simple-alert.sh") | crontab -
    echo "✅ 헬스체크가 5분마다 실행됩니다"
    ;;
  3)
    echo "🚀 모든 cron 작업 설정 중..."
    (crontab -l 2>/dev/null; cat << 'EOF'
# DreamSeed AI 자동화
0 9 * * * /home/won/projects/dreamseed_monorepo/daily-report.sh
*/5 * * * * /home/won/projects/dreamseed_monorepo/simple-alert.sh
0 18 * * * /home/won/projects/dreamseed_monorepo/6line-summary.sh >> /tmp/daily-analysis.log
0 8 * * 1 /home/won/projects/dreamseed_monorepo/cache-monitor.sh
EOF
    ) | crontab -
    echo "✅ 모든 자동화 작업이 설정되었습니다"
    ;;
  4)
    echo "📝 사용자 정의 cron 설정"
    echo "현재 cron 작업을 편집하시겠습니까? (y/n)"
    read -p "선택: " EDIT_CHOICE
    if [ "$EDIT_CHOICE" = "y" ] || [ "$EDIT_CHOICE" = "Y" ]; then
      crontab -e
    fi
    ;;
  5)
    echo "❌ cron 설정을 취소했습니다"
    exit 0
    ;;
  *)
    echo "❌ 잘못된 선택입니다"
    exit 1
    ;;
esac

echo ""

# 설정된 cron 작업 확인
echo "📋 설정된 cron 작업:"
crontab -l

echo ""

# Slack 웹훅 설정 안내
echo "🔔 Slack 알림 설정 안내"
echo "========================"
echo "Slack 알림을 받으려면 SLACK_WEBHOOK_URL을 설정하세요:"
echo ""
echo "export SLACK_WEBHOOK_URL='https://hooks.slack.com/services/...'"
echo "echo 'export SLACK_WEBHOOK_URL=\"https://hooks.slack.com/services/...\"' >> ~/.bashrc"
echo ""

# 테스트 실행
echo "🧪 테스트 실행"
echo "==============="
echo "설정한 cron 작업을 테스트해보시겠습니까? (y/n)"
read -p "선택: " TEST_CHOICE

if [ "$TEST_CHOICE" = "y" ] || [ "$TEST_CHOICE" = "Y" ]; then
  echo "📊 6줄 요약 테스트..."
  ./6line-summary.sh
  
  echo ""
  echo "📤 일일 리포트 테스트..."
  ./daily-report.sh
  
  echo ""
  echo "🔍 헬스체크 테스트..."
  ./simple-alert.sh
fi

echo ""
echo "🎯 cron 자동화 설정 완료!"
echo "💡 cron 작업 확인: crontab -l"
echo "💡 cron 로그 확인: tail -f /var/log/cron"
