#!/bin/bash

# 🔍 진단 포인트 (컨테이너 종료 시 90% 원인 파악)

set -e

echo "🔍 DreamSeed AI 진단 시작"
echo "================================"

# 1) 컨테이너 상태 확인
echo "1️⃣ 컨테이너 상태"
echo "-------------------"
docker ps --filter name=dreamseed- --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}' 2>/dev/null || echo "실행 중인 컨테이너 없음"

echo ""

# 2) 최근 종료된 컨테이너 로그
echo "2️⃣ 최근 종료된 컨테이너 로그"
echo "----------------------------"
RECENT_CONTAINER=$(docker ps -a --filter name=dreamseed- --format '{{.Names}}' | head -1)
if [ -n "$RECENT_CONTAINER" ]; then
  echo "📋 컨테이너: $RECENT_CONTAINER"
  echo "로그 (최근 50줄):"
  docker logs $RECENT_CONTAINER --tail 50 2>/dev/null || echo "로그 없음"
else
  echo "최근 종료된 컨테이너 없음"
fi

echo ""

# 3) 시스템 로그 (OOM Kill 여부)
echo "3️⃣ 시스템 로그 (OOM Kill 여부)"
echo "-----------------------------"
dmesg | tail -n 50 | grep -E "(OOM|killed|error|fail)" || echo "시스템 로그 정상"

echo ""

# 4) GPU 상태
echo "4️⃣ GPU 상태"
echo "-------------"
nvidia-smi --query-gpu=name,memory.used,memory.total,utilization.gpu,temperature.gpu --format=csv,noheader,nounits | \
awk -F',' '{printf "GPU: %s\n메모리: %dMB / %dMB (%.1f%%)\n사용률: %d%%\n온도: %d°C\n", $1, $2, $3, ($2/$3)*100, $4, $5}'

echo ""

# 5) 디스크 여유 공간
echo "5️⃣ 디스크 여유 공간"
echo "-------------------"
df -h | grep -E "(/$|/home)" | awk '{printf "파티션: %s, 사용: %s / %s (%s), 여유: %s\n", $6, $3, $2, $5, $4}'

echo ""

# 6) 포트 사용 상태
echo "6️⃣ 포트 사용 상태"
echo "-----------------"
netstat -tlnp | grep -E ":800[0-2]" || echo "포트 8000-8002 사용 중"

echo ""

# 7) 캐시 디렉터리 상태
echo "7️⃣ 캐시 디렉터리 상태"
echo "---------------------"
if [ -d "$HOME/.cache/huggingface" ]; then
  CACHE_SIZE=$(du -sh $HOME/.cache/huggingface 2>/dev/null | cut -f1)
  echo "캐시 크기: $CACHE_SIZE"
  echo "권한: $(ls -ld $HOME/.cache/huggingface | awk '{print $1, $3, $4}')"
else
  echo "캐시 디렉터리 없음"
fi

echo ""

# 8) 네트워크 연결 테스트
echo "8️⃣ 네트워크 연결 테스트"
echo "-----------------------"
echo "Hugging Face 연결 테스트:"
if curl -s --connect-timeout 10 https://huggingface.co > /dev/null; then
  echo "✅ Hugging Face 연결 정상"
else
  echo "❌ Hugging Face 연결 실패"
fi

echo ""

# 9) 메모리 사용량
echo "9️⃣ 메모리 사용량"
echo "----------------"
free -h | awk 'NR==2{printf "메모리: %s / %s (%.1f%% 사용)\n", $3, $2, ($3/$2)*100}'

echo ""

# 10) 권장 해결책
echo "🔧 권장 해결책"
echo "==============="

# OOM 체크
if dmesg | tail -n 100 | grep -q "Out of memory\|oom-killer"; then
  echo "🚨 OOM 감지됨:"
  echo "   - --gpu-memory-utilization 낮추기 (0.82 → 0.75)"
  echo "   - --max-model-len 낮추기 (6144 → 4096)"
  echo "   - --max-num-seqs 낮추기 (16 → 8)"
fi

# 디스크 부족 체크
DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 90 ]; then
  echo "🚨 디스크 부족:"
  echo "   - 캐시 정리: rm -rf ~/.cache/huggingface/*"
  echo "   - 불필요한 이미지 정리: docker system prune"
fi

# GPU 메모리 부족 체크
GPU_MEMORY=$(nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader,nounits | awk -F',' '{printf "%.1f", ($1/$2)*100}')
if (( $(echo "$GPU_MEMORY > 95" | bc -l) )); then
  echo "🚨 GPU 메모리 부족:"
  echo "   - --gpu-memory-utilization 낮추기"
  echo "   - 다른 프로세스 종료"
fi

echo ""
echo "🎯 진단 완료!"
echo "💡 문제 해결 후: ./start-profile-s.sh로 재시작"
