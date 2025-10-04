#!/bin/bash

# 🟢 프로필 S 정지 스크립트

set -e

echo "🛑 프로필 S 정지 중..."

# 7B 모델 정지
echo "🤖 7B 모델들 정지 중..."
docker stop dreamseed-mistral-7b dreamseed-qwen2-7b dreamseed-phi3-mini 2>/dev/null || true
docker rm dreamseed-mistral-7b dreamseed-qwen2-7b dreamseed-phi3-mini 2>/dev/null || true

# 상태 확인
echo "📊 정지 후 상태:"
echo "컨테이너: $(docker ps --filter name=dreamseed- --format 'table {{.Names}}\t{{.Status}}' 2>/dev/null || echo '없음')"
echo "GPU 메모리:"
nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader,nounits | awk '{printf "  사용: %dMB / %dMB (%.1f%%)\n", $1, $2, ($1/$2)*100}'

echo ""
echo "✅ 프로필 S 정지 완료!"
echo "💡 재시작: ./start-profile-s.sh"
