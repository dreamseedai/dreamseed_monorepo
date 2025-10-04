#!/bin/bash

# 🧪 부하 스모크 테스트
# 5회 연속 ping으로 에러율/지연 확인

set -e

echo "🧪 부하 스모크 테스트 시작"
echo "================================"

# 모델명 확인
echo "📋 모델 정보 확인 중..."
MODEL_RESPONSE=$(curl -s http://127.0.0.1:8000/v1/models 2>/dev/null)
if [ $? -ne 0 ] || ! echo "$MODEL_RESPONSE" | jq -e '.data[0].id' > /dev/null 2>&1; then
  echo "❌ 모델 API 응답 실패"
  exit 1
fi

MODEL_NAME=$(echo "$MODEL_RESPONSE" | jq -r '.data[0].id')
echo "✅ 모델: $MODEL_NAME"

echo ""
echo "🚀 5회 연속 ping 테스트 시작..."
echo "--------------------------------"

# 성공/실패 카운터
SUCCESS_COUNT=0
FAIL_COUNT=0
TOTAL_TIME=0

# 5회 연속 테스트
for i in {1..5}; do
  echo -n "테스트 $i/5: "
  
  # 시간 측정과 함께 요청
  START_TIME=$(date +%s.%N)
  RESPONSE=$(curl -s -w "%{http_code}" -X POST http://127.0.0.1:8000/v1/chat/completions \
    -H 'Content-Type: application/json' \
    -H 'Authorization: Bearer dummy' \
    -d "{\"model\":\"$MODEL_NAME\", \"messages\":[{\"role\":\"user\",\"content\":\"ping\"}], \"max_tokens\":4}" 2>/dev/null)
  END_TIME=$(date +%s.%N)
  
  # 응답 시간 계산
  DURATION=$(echo "$END_TIME - $START_TIME" | bc -l 2>/dev/null || echo "0")
  DURATION_MS=$(echo "$DURATION * 1000" | bc -l 2>/dev/null || echo "0")
  
  # HTTP 상태 코드 추출
  HTTP_CODE=$(echo "$RESPONSE" | tail -c 4)
  RESPONSE_BODY=$(echo "$RESPONSE" | head -c -4)
  
  if [ "$HTTP_CODE" = "200" ] && echo "$RESPONSE_BODY" | jq -e '.choices[0].message.content' > /dev/null 2>&1; then
    CONTENT=$(echo "$RESPONSE_BODY" | jq -r '.choices[0].message.content')
    echo "✅ 성공 (${DURATION_MS}ms) - $CONTENT"
    SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
    TOTAL_TIME=$(echo "$TOTAL_TIME + $DURATION" | bc -l 2>/dev/null || echo "$TOTAL_TIME")
  else
    echo "❌ 실패 (HTTP: $HTTP_CODE)"
    FAIL_COUNT=$((FAIL_COUNT + 1))
  fi
  
  # 1초 대기
  sleep 1
done

echo ""
echo "📊 테스트 결과"
echo "=============="
echo "✅ 성공: $SUCCESS_COUNT/5"
echo "❌ 실패: $FAIL_COUNT/5"
echo "📈 성공률: $((SUCCESS_COUNT * 100 / 5))%"

if [ $SUCCESS_COUNT -gt 0 ]; then
  AVG_TIME=$(echo "scale=2; $TOTAL_TIME / $SUCCESS_COUNT * 1000" | bc -l 2>/dev/null || echo "0")
  echo "⏱️  평균 응답시간: ${AVG_TIME}ms"
fi

echo ""
if [ $FAIL_COUNT -eq 0 ]; then
  echo "🎉 모든 테스트 통과! 시스템 정상"
elif [ $FAIL_COUNT -le 2 ]; then
  echo "⚠️  일부 실패 - 모니터링 필요"
else
  echo "🚨 다수 실패 - 즉시 점검 필요"
fi

echo ""
echo "💡 문제 발생 시: ./health-check-60s.sh 실행"
