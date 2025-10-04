#!/bin/bash

# 🧪 프로필 S 테스트 스크립트

set -e

echo "🧪 프로필 S 테스트 시작"

# 기본 헬스체크
echo "1️⃣ 기본 헬스체크..."
if curl -s http://127.0.0.1:8000/v1/models > /dev/null 2>&1; then
  echo "✅ 8B 모델 응답 정상"
else
  echo "❌ 8B 모델 응답 실패"
  exit 1
fi

# 모델 정보 확인
echo "2️⃣ 모델 정보 확인..."
MODEL_INFO=$(curl -s http://127.0.0.1:8000/v1/models | jq -r '.data[0].id')
echo "📋 로드된 모델: $MODEL_INFO"
echo "💡 실제 모델: meta-llama/Llama-3.1-8B-Instruct (vLLM API에서는 다른 이름으로 표시)"

# 간단한 채팅 테스트
echo "3️⃣ 채팅 테스트..."
RESPONSE=$(curl -s -X POST http://127.0.0.1:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "'$MODEL_INFO'",
    "messages": [
      {"role": "user", "content": "안녕하세요! DreamSeedAI Guide 기능을 한 문단으로 설명해줘."}
    ],
    "max_tokens": 200,
    "temperature": 0.7
  }')

if echo "$RESPONSE" | jq -e '.choices[0].message.content' > /dev/null 2>&1; then
  CONTENT=$(echo "$RESPONSE" | jq -r '.choices[0].message.content')
  echo "✅ 채팅 응답 성공: $CONTENT"
else
  echo "❌ 채팅 응답 실패"
  echo "$RESPONSE" | jq . 2>/dev/null || echo "$RESPONSE"
  exit 1
fi

# GPU 메모리 확인
echo "4️⃣ GPU 메모리 확인..."
GPU_MEMORY=$(nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader,nounits)
USED=$(echo $GPU_MEMORY | cut -d',' -f1 | tr -d ' ')
TOTAL=$(echo $GPU_MEMORY | cut -d',' -f2 | tr -d ' ')
USAGE_PERCENT=$((USED * 100 / TOTAL))
echo "📊 GPU 메모리: ${USED}MB / ${TOTAL}MB (${USAGE_PERCENT}%)"

if [ $USAGE_PERCENT -gt 90 ]; then
  echo "⚠️  GPU 메모리 사용률이 높습니다 (${USAGE_PERCENT}%)"
else
  echo "✅ GPU 메모리 사용률 정상 (${USAGE_PERCENT}%)"
fi

# 컨테이너 상태 확인
echo "5️⃣ 컨테이너 상태 확인..."
CONTAINER_STATUS=$(docker ps --filter name=dreamseed-llama-8b --format '{{.Status}}')
if [ -n "$CONTAINER_STATUS" ]; then
  echo "✅ 컨테이너 실행 중: $CONTAINER_STATUS"
else
  echo "❌ 컨테이너가 실행되지 않음"
  exit 1
fi

echo ""
echo "🎉 프로필 S 테스트 완료!"
echo "📍 엔드포인트: http://127.0.0.1:8000"
echo "🔧 라우터 연동 준비 완료"
