#!/bin/bash

# 🧪 일일 리포트 자동화 (cron으로 하루 1회 실행 → Slack으로 붙여 숫자만 알림)

set -e

echo "🧪 DreamSeed AI 일일 리포트 생성"
echo "=================================="

# 6줄 요약 실행
SUMMARY_OUTPUT=$(./6line-summary.sh 2>/dev/null | grep -A 10 "운영 데이터 6줄 요약")

# 6줄 데이터 추출
P95_LATENCY=$(echo "$SUMMARY_OUTPUT" | grep "P95_latency_ms:" | cut -d' ' -f2)
ERROR_RATE=$(echo "$SUMMARY_OUTPUT" | grep "Error_rate_percent:" | cut -d' ' -f2)
GPU_VRAM_MAX=$(echo "$SUMMARY_OUTPUT" | grep "GPU_VRAM_max_percent:" | cut -d' ' -f2)
TOKENS=$(echo "$SUMMARY_OUTPUT" | grep "Avg_tokens_in/out:" | cut -d' ' -f2)
FAST_RATIO=$(echo "$SUMMARY_OUTPUT" | grep "Fast_lane_ratio_percent:" | cut -d' ' -f2)
CODE_RATIO=$(echo "$SUMMARY_OUTPUT" | grep "Code_lane_ratio_percent:" | cut -d' ' -f2)

# 날짜
DATE=$(date '+%Y-%m-%d')

echo "📊 일일 리포트 ($DATE)"
echo "======================"
echo "P95_latency_ms: $P95_LATENCY"
echo "Error_rate_percent: $ERROR_RATE"
echo "GPU_VRAM_max_percent: $GPU_VRAM_MAX"
echo "Avg_tokens_in/out: $TOKENS"
echo "Fast_lane_ratio_percent: $FAST_RATIO"
echo "Code_lane_ratio_percent: $CODE_RATIO"

# Slack 웹훅이 설정되어 있으면 전송
if [ -n "$SLACK_WEBHOOK_URL" ]; then
  echo ""
  echo "📤 Slack 알림 전송 중..."
  
  # 상태 이모지 결정
  if [ $P95_LATENCY -le 200 ] && [ $ERROR_RATE -le 1 ] && [ $GPU_VRAM_MAX -le 90 ]; then
    STATUS_EMOJI="✅"
    STATUS_TEXT="정상"
  elif [ $ERROR_RATE -gt 5 ] || [ $GPU_VRAM_MAX -gt 95 ]; then
    STATUS_EMOJI="🚨"
    STATUS_TEXT="주의"
  else
    STATUS_EMOJI="⚠️"
    STATUS_TEXT="모니터링"
  fi
  
  # Slack 메시지 전송
  curl -X POST -H 'Content-type: application/json' "$SLACK_WEBHOOK_URL" \
    -d "{
      \"text\": \"${STATUS_EMOJI} [DreamSeedAI] 일일 리포트 ($DATE) - ${STATUS_TEXT}\",
      \"attachments\": [{
        \"color\": \"${STATUS_EMOJI == "✅" ? "good" : (STATUS_EMOJI == "🚨" ? "danger" : "warning")}\",
        \"fields\": [
          {\"title\": \"P95 지연\", \"value\": \"${P95_LATENCY}ms\", \"short\": true},
          {\"title\": \"에러율\", \"value\": \"${ERROR_RATE}%\", \"short\": true},
          {\"title\": \"GPU VRAM\", \"value\": \"${GPU_VRAM_MAX}%\", \"short\": true},
          {\"title\": \"토큰\", \"value\": \"${TOKENS}\", \"short\": true},
          {\"title\": \"Fast 비율\", \"value\": \"${FAST_RATIO}%\", \"short\": true},
          {\"title\": \"Code 비율\", \"value\": \"${CODE_RATIO}%\", \"short\": true}
        ],
        \"footer\": \"DreamSeed AI\",
        \"ts\": $(date +%s)
      }]
    }" > /dev/null 2>&1
  
  if [ $? -eq 0 ]; then
    echo "✅ Slack 알림 전송 완료"
  else
    echo "❌ Slack 알림 전송 실패"
  fi
else
  echo ""
  echo "ℹ️  SLACK_WEBHOOK_URL이 설정되지 않았습니다"
  echo "   설정: export SLACK_WEBHOOK_URL='https://hooks.slack.com/services/...'"
fi

# 로그 파일에 저장
LOG_FILE="/tmp/daily-reports.log"
echo "$DATE: P95=${P95_LATENCY}ms, Error=${ERROR_RATE}%, VRAM=${GPU_VRAM_MAX}%, Tokens=${TOKENS}, Fast=${FAST_RATIO}%, Code=${CODE_RATIO}%" >> "$LOG_FILE"

echo ""
echo "🎯 일일 리포트 완료!"
echo "💡 로그 저장: $LOG_FILE"
