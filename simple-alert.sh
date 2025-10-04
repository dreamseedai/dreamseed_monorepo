#!/bin/bash

# 🔔 실패 알림 (간단)
# health-check-60s.sh가 실패하면 Slack 웹훅으로 단 한 줄만 전송

set -e

# Slack 웹훅 URL 확인
if [ -z "$SLACK_WEBHOOK_URL" ]; then
  echo "❌ SLACK_WEBHOOK_URL이 설정되지 않았습니다."
  echo "💡 설정: export SLACK_WEBHOOK_URL='https://hooks.slack.com/services/...'"
  exit 1
fi

# 헬스체크 실행
echo "🔍 헬스체크 실행 중..."
if ./health-check-60s.sh > /dev/null 2>&1; then
  echo "✅ 헬스체크 성공"
  exit 0
else
  echo "❌ 헬스체크 실패"
  
  # Slack 알림 전송
  echo "📤 Slack 알림 전송 중..."
  curl -X POST -H 'Content-type: application/json' "$SLACK_WEBHOOK_URL" \
    -d "{\"text\":\"[DreamSeedAI] Health check FAIL at $(date -Is)\"}" \
    > /dev/null 2>&1
  
  if [ $? -eq 0 ]; then
    echo "✅ Slack 알림 전송 완료"
  else
    echo "❌ Slack 알림 전송 실패"
  fi
  
  exit 1
fi
