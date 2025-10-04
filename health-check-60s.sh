#!/bin/bash

# ⏱️ 60초 점검 루틴
# 컨테이너 종료/지연 악화 감지 시 원인 90% 파악

set -e

echo "🔍 60초 점검 루틴 시작"
echo "================================"

# 1) GPU/메모리 상태
echo "1️⃣ GPU/메모리 상태"
echo "-------------------"
nvidia-smi --query-gpu=name,memory.used,memory.total,utilization.gpu --format=csv,noheader,nounits | \
awk -F',' '{printf "GPU: %s\n메모리: %dMB / %dMB (%.1f%%)\n사용률: %d%%\n", $1, $2, $3, ($2/$3)*100, $4}'

echo ""

# 2) vLLM 컨테이너 로그 (최근 200줄)
echo "2️⃣ vLLM 컨테이너 로그 (최근 20줄)"
echo "--------------------------------"
CONTAINER_ID=$(docker ps -q --filter name=dreamseed-llama-8b)
if [ -n "$CONTAINER_ID" ]; then
  echo "✅ 컨테이너 실행 중: $CONTAINER_ID"
  docker logs $CONTAINER_ID --tail 20
else
  echo "❌ 컨테이너가 실행되지 않음"
  echo "전체 컨테이너 목록:"
  docker ps -a --filter name=dreamseed- | head -5
fi

echo ""

# 3) 헬스 체크
echo "3️⃣ 헬스 체크"
echo "-------------"

# 모델 목록 확인
echo "📋 모델 목록:"
MODEL_RESPONSE=$(curl -s http://127.0.0.1:8000/v1/models 2>/dev/null)
if [ $? -eq 0 ] && echo "$MODEL_RESPONSE" | jq -e '.data[0].id' > /dev/null 2>&1; then
  MODEL_NAME=$(echo "$MODEL_RESPONSE" | jq -r '.data[0].id')
  echo "✅ 모델 응답 정상: $MODEL_NAME"
  
  # 간단한 채팅 테스트
  echo "💬 채팅 테스트:"
  CHAT_RESPONSE=$(curl -s -X POST http://127.0.0.1:8000/v1/chat/completions \
    -H 'Content-Type: application/json' \
    -H 'Authorization: Bearer dummy' \
    -d "{\"model\":\"$MODEL_NAME\", \"messages\":[{\"role\":\"user\",\"content\":\"ping\"}], \"max_tokens\":8}" 2>/dev/null)
  
  if echo "$CHAT_RESPONSE" | jq -e '.choices[0].message.content' > /dev/null 2>&1; then
    CONTENT=$(echo "$CHAT_RESPONSE" | jq -r '.choices[0].message.content')
    echo "✅ 채팅 응답 성공: $CONTENT"
  else
    echo "❌ 채팅 응답 실패"
    echo "$CHAT_RESPONSE" | jq . 2>/dev/null || echo "$CHAT_RESPONSE"
  fi
else
  echo "❌ 모델 API 응답 실패"
  echo "$MODEL_RESPONSE" 2>/dev/null || echo "연결 실패"
fi

echo ""

# 4) 시스템 로그 (필요시)
echo "4️⃣ 시스템 로그 (최근 10줄)"
echo "-------------------------"
dmesg | tail -n 10 | grep -E "(OOM|killed|error|fail)" || echo "시스템 로그 정상"

echo ""

# 5) 포트 상태
echo "5️⃣ 포트 상태"
echo "-------------"
netstat -tlnp | grep -E ":800[0-2]" || echo "포트 8000-8002 사용 중"

echo ""
echo "🎯 점검 완료!"
echo "💡 문제 발견 시:"
echo "   - OOM: --max-model-len 낮추기, --gpu-memory-utilization 0.80~0.85"
echo "   - HF 다운로드 실패: 토큰/네트워크 확인, 캐시 볼륨 유지"
echo "   - 권한/포트: 포트 변경/권한 확인"
