#!/bin/bash

# 🔔 알림 한 줄 연결 (에러/타임아웃 감지)
# health-check-60s.sh/diagnose-issues.sh의 실패 패턴을 Slack 웹훅에 POST

set -e

echo "🔔 알림 설정 가이드"
echo "================================"

# Slack 웹훅 URL 설정
echo "1️⃣ Slack 웹훅 URL 설정"
echo "-----------------------"
echo "Slack 웹훅 URL을 입력하세요 (선택사항):"
echo "예: https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX"
echo ""
echo "설정하지 않으면 로컬 로그만 출력됩니다."
echo ""

# 환경변수 설정
read -p "Slack 웹훅 URL (엔터로 건너뛰기): " SLACK_WEBHOOK_URL

if [ -n "$SLACK_WEBHOOK_URL" ]; then
  echo "export SLACK_WEBHOOK_URL=\"$SLACK_WEBHOOK_URL\"" >> ~/.bashrc
  echo "✅ Slack 웹훅 URL이 설정되었습니다"
else
  echo "ℹ️  Slack 웹훅 URL을 건너뛰었습니다 (로컬 로그만 사용)"
fi

echo ""

# 알림 함수 생성
echo "2️⃣ 알림 함수 생성"
echo "-------------------"

# 알림 함수를 별도 파일로 생성
cat > /home/won/projects/dreamseed_monorepo/send-notification.sh << 'EOF'
#!/bin/bash

# 🔔 알림 전송 함수
# 사용법: ./send-notification.sh "제목" "메시지" "레벨"

TITLE="$1"
MESSAGE="$2"
LEVEL="${3:-info}"

# 타임스탬프
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# 로컬 로그 출력
case $LEVEL in
  "error")
    echo "🚨 [$TIMESTAMP] $TITLE: $MESSAGE" | tee -a /tmp/dreamseed-errors.log
    ;;
  "warning")
    echo "⚠️  [$TIMESTAMP] $TITLE: $MESSAGE" | tee -a /tmp/dreamseed-warnings.log
    ;;
  *)
    echo "ℹ️  [$TIMESTAMP] $TITLE: $MESSAGE" | tee -a /tmp/dreamseed-info.log
    ;;
esac

# Slack 웹훅이 설정되어 있으면 전송
if [ -n "$SLACK_WEBHOOK_URL" ]; then
  # 색상 설정
  case $LEVEL in
    "error")
      COLOR="danger"
      EMOJI="🚨"
      ;;
    "warning")
      COLOR="warning"
      EMOJI="⚠️"
      ;;
    *)
      COLOR="good"
      EMOJI="ℹ️"
      ;;
  esac
  
  # Slack 메시지 전송
  curl -s -X POST "$SLACK_WEBHOOK_URL" \
    -H 'Content-type: application/json' \
    --data "{
      \"attachments\": [{
        \"color\": \"$COLOR\",
        \"title\": \"$EMOJI $TITLE\",
        \"text\": \"$MESSAGE\",
        \"footer\": \"DreamSeed AI\",
        \"ts\": $(date +%s)
      }]
    }" > /dev/null 2>&1
fi
EOF

chmod +x /home/won/projects/dreamseed_monorepo/send-notification.sh
echo "✅ 알림 함수가 생성되었습니다: send-notification.sh"

echo ""

# health-check-60s.sh에 알림 추가
echo "3️⃣ 헬스체크에 알림 추가"
echo "-------------------------"

# 기존 health-check-60s.sh에 알림 추가
if [ -f "/home/won/projects/dreamseed_monorepo/health-check-60s.sh" ]; then
  # 알림 함수 import 추가
  sed -i '1a # 알림 함수 import\nsource /home/won/projects/dreamseed_monorepo/send-notification.sh' /home/won/projects/dreamseed_monorepo/health-check-60s.sh
  
  # 실패 시 알림 추가
  sed -i '/❌ 8B 모델 응답 실패/a \ \ ./send-notification.sh "모델 API 실패" "8B 모델이 응답하지 않습니다" "error"' /home/won/projects/dreamseed_monorepo/health-check-60s.sh
  sed -i '/❌ 채팅 응답 실패/a \ \ ./send-notification.sh "채팅 API 실패" "채팅 요청이 실패했습니다" "error"' /home/won/projects/dreamseed_monorepo/health-check-60s.sh
  sed -i '/❌ 컨테이너가 실행되지 않음/a \ \ ./send-notification.sh "컨테이너 종료" "vLLM 컨테이너가 실행되지 않습니다" "error"' /home/won/projects/dreamseed_monorepo/health-check-60s.sh
  
  echo "✅ health-check-60s.sh에 알림이 추가되었습니다"
else
  echo "⚠️  health-check-60s.sh를 찾을 수 없습니다"
fi

echo ""

# diagnose-issues.sh에 알림 추가
echo "4️⃣ 진단 스크립트에 알림 추가"
echo "-----------------------------"

if [ -f "/home/won/projects/dreamseed_monorepo/diagnose-issues.sh" ]; then
  # 알림 함수 import 추가
  sed -i '1a # 알림 함수 import\nsource /home/won/projects/dreamseed_monorepo/send-notification.sh' /home/won/projects/dreamseed_monorepo/diagnose-issues.sh
  
  # OOM 감지 시 알림 추가
  sed -i '/OOM 감지됨:/a \ \ ./send-notification.sh "OOM 감지" "시스템 메모리 부족으로 프로세스가 종료되었습니다" "error"' /home/won/projects/dreamseed_monorepo/diagnose-issues.sh
  
  # 디스크 부족 시 알림 추가
  sed -i '/디스크 부족:/a \ \ ./send-notification.sh "디스크 부족" "디스크 사용량이 90%를 초과했습니다" "warning"' /home/won/projects/dreamseed_monorepo/diagnose-issues.sh
  
  # GPU 메모리 부족 시 알림 추가
  sed -i '/GPU 메모리 부족:/a \ \ ./send-notification.sh "GPU 메모리 부족" "GPU 메모리 사용량이 95%를 초과했습니다" "warning"' /home/won/projects/dreamseed_monorepo/diagnose-issues.sh
  
  echo "✅ diagnose-issues.sh에 알림이 추가되었습니다"
else
  echo "⚠️  diagnose-issues.sh를 찾을 수 없습니다"
fi

echo ""

# 테스트 알림
echo "5️⃣ 테스트 알림"
echo "---------------"
echo "테스트 알림을 전송하시겠습니까? (y/n)"
read -p "선택: " TEST_NOTIFICATION

if [ "$TEST_NOTIFICATION" = "y" ] || [ "$TEST_NOTIFICATION" = "Y" ]; then
  ./send-notification.sh "테스트 알림" "DreamSeed AI 알림 시스템이 정상적으로 작동합니다" "info"
  echo "✅ 테스트 알림이 전송되었습니다"
else
  echo "ℹ️  테스트 알림을 건너뛰었습니다"
fi

echo ""
echo "🎯 알림 설정 완료!"
echo "=================="
echo "✅ Slack 웹훅: ${SLACK_WEBHOOK_URL:-'설정되지 않음 (로컬 로그만 사용)'}"
echo "✅ 알림 함수: send-notification.sh"
echo "✅ 헬스체크 알림: health-check-60s.sh"
echo "✅ 진단 알림: diagnose-issues.sh"
echo ""
echo "💡 사용법:"
echo "   ./send-notification.sh \"제목\" \"메시지\" \"레벨\""
echo "   레벨: info, warning, error"
echo ""
echo "💡 로그 확인:"
echo "   tail -f /tmp/dreamseed-*.log"
