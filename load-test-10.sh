#!/bin/bash

# 🧪 짧은 부하 리허설 (10회)
# 실행 시간 평균이 높으면 max-model-len↓ 또는 max-num-seqs↓로 즉시 체감 개선

set -e

echo "🧪 부하 리허설 시작 (10회)"
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
echo "🚀 10회 연속 부하 테스트 시작..."
echo "--------------------------------"

# 성공/실패 카운터
SUCCESS_COUNT=0
FAIL_COUNT=0
TOTAL_TIME=0
TIMES=()

# 10회 연속 테스트
for i in {1..10}; do
  echo -n "테스트 $i/10: "
  
  # 시간 측정과 함께 요청
  START_TIME=$(date +%s.%N)
  RESPONSE=$(curl -s -w "%{http_code}" -X POST http://127.0.0.1:8000/v1/chat/completions \
    -H 'Content-Type: application/json' \
    -H 'Authorization: Bearer dummy' \
    -d "{\"model\":\"$MODEL_NAME\", \"messages\":[{\"role\":\"user\",\"content\":\"ping\"}], \"max_tokens\":8}" 2>/dev/null)
  END_TIME=$(date +%s.%N)
  
  # 응답 시간 계산
  DURATION=$(echo "$END_TIME - $START_TIME" | bc -l 2>/dev/null || echo "0")
  DURATION_MS=$(echo "$DURATION * 1000" | bc -l 2>/dev/null || echo "0")
  TIMES+=($DURATION_MS)
  
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
  
  # 0.5초 대기
  sleep 0.5
done

echo ""
echo "📊 부하 테스트 결과"
echo "=================="
echo "✅ 성공: $SUCCESS_COUNT/10"
echo "❌ 실패: $FAIL_COUNT/10"
echo "📈 성공률: $((SUCCESS_COUNT * 100 / 10))%"

if [ $SUCCESS_COUNT -gt 0 ]; then
  AVG_TIME=$(echo "scale=2; $TOTAL_TIME / $SUCCESS_COUNT * 1000" | bc -l 2>/dev/null || echo "0")
  echo "⏱️  평균 응답시간: ${AVG_TIME}ms"
  
  # P95 계산 (간단한 버전)
  IFS=$'\n' SORTED_TIMES=($(sort -n <<<"${TIMES[*]}"))
  P95_INDEX=$((SUCCESS_COUNT * 95 / 100))
  P95_TIME=${SORTED_TIMES[$P95_INDEX]}
  echo "📊 P95 응답시간: ${P95_TIME}ms"
fi

echo ""
echo "🔧 성능 개선 권장사항"
echo "===================="

if [ $SUCCESS_COUNT -gt 0 ]; then
  if (( $(echo "$AVG_TIME > 100" | bc -l) )); then
    echo "⚠️  평균 응답시간이 높습니다 (${AVG_TIME}ms)"
    echo "   권장: --max-model-len 6144 → 4096"
    echo "   권장: --max-num-seqs 16 → 12"
  elif (( $(echo "$AVG_TIME < 50" | bc -l) )); then
    echo "✅ 응답시간이 빠릅니다 (${AVG_TIME}ms)"
    echo "   여유가 있다면: --max-num-seqs 16 → 20 (스루풋↑)"
  else
    echo "✅ 응답시간이 적절합니다 (${AVG_TIME}ms)"
  fi
  
  if [ -n "$P95_TIME" ] && (( $(echo "$P95_TIME > 200" | bc -l) )); then
    echo "⚠️  P95 응답시간이 높습니다 (${P95_TIME}ms)"
    echo "   권장: --max-model-len 6144 → 4096"
  fi
fi

if [ $FAIL_COUNT -gt 2 ]; then
  echo "🚨 실패율이 높습니다 ($FAIL_COUNT/10)"
  echo "   권장: ./diagnose-issues.sh 실행"
  echo "   권장: --gpu-memory-utilization 0.82 → 0.75"
fi

echo ""
if [ $FAIL_COUNT -eq 0 ] && [ $SUCCESS_COUNT -gt 0 ]; then
  echo "🎉 모든 테스트 통과! 성능 최적화 완료"
elif [ $FAIL_COUNT -le 2 ]; then
  echo "⚠️  일부 실패 - 모니터링 필요"
else
  echo "🚨 다수 실패 - 즉시 점검 필요"
fi

echo ""
echo "💡 문제 발생 시: ./diagnose-issues.sh 실행"
