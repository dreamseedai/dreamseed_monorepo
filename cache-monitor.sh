#!/bin/bash

# 📊 모델 캐시/디스크 상태 모니터
# 캐시 정리 기준: 50GB 이상일 때 purge

set -e

echo "📊 캐시/디스크 상태 모니터"
echo "================================"

# 1) 디스크 사용량
echo "1️⃣ 디스크 사용량"
echo "-------------------"
df -h | awk 'NR==1 || /cache|home|\/$/' | while read line; do
  echo "$line"
done

echo ""

# 2) HF 캐시 크기
echo "2️⃣ Hugging Face 캐시"
echo "---------------------"
if [ -d "$HOME/.cache/huggingface" ]; then
  CACHE_SIZE=$(du -sh $HOME/.cache/huggingface 2>/dev/null | cut -f1)
  CACHE_SIZE_GB=$(du -sg $HOME/.cache/huggingface 2>/dev/null | cut -f1)
  echo "📁 캐시 크기: $CACHE_SIZE"
  echo "📁 권한: $(ls -ld $HOME/.cache/huggingface | awk '{print $1, $3, $4}')"
  
  # 캐시 정리 기준 체크
  if [ -n "$CACHE_SIZE_GB" ] && [ $CACHE_SIZE_GB -gt 50 ]; then
    echo "⚠️  캐시 크기가 50GB를 초과했습니다 ($CACHE_SIZE_GB GB)"
    echo "   권장: 캐시 정리 실행"
  else
    echo "✅ 캐시 크기 정상 ($CACHE_SIZE_GB GB)"
  fi
else
  echo "❌ 캐시 디렉터리 없음"
fi

echo ""

# 3) 캐시 내용 분석
echo "3️⃣ 캐시 내용 분석"
echo "-------------------"
if [ -d "$HOME/.cache/huggingface/hub" ]; then
  echo "📋 다운로드된 모델들:"
  find $HOME/.cache/huggingface/hub -maxdepth 2 -type d -name "models--*" 2>/dev/null | while read model_dir; do
    MODEL_NAME=$(basename "$model_dir" | sed 's/models--//' | sed 's/--/\//')
    MODEL_SIZE=$(du -sh "$model_dir" 2>/dev/null | cut -f1)
    echo "  - $MODEL_NAME: $MODEL_SIZE"
  done
else
  echo "❌ 모델 캐시 없음"
fi

echo ""

# 4) Docker 이미지 크기
echo "4️⃣ Docker 이미지 크기"
echo "----------------------"
docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}" | grep -E "(vllm|dreamseed)" || echo "관련 이미지 없음"

echo ""

# 5) 시스템 메모리
echo "5️⃣ 시스템 메모리"
echo "-----------------"
free -h | awk 'NR==2{printf "메모리: %s / %s (%.1f%% 사용)\n", $3, $2, ($3/$2)*100}'

echo ""

# 6) 권장 정리 작업
echo "🔧 권장 정리 작업"
echo "=================="

# 캐시 정리 기준 체크
if [ -d "$HOME/.cache/huggingface" ]; then
  CACHE_SIZE_GB=$(du -sg $HOME/.cache/huggingface 2>/dev/null | cut -f1)
  if [ -n "$CACHE_SIZE_GB" ] && [ $CACHE_SIZE_GB -gt 50 ]; then
    echo "🧹 캐시 정리 필요 (현재: ${CACHE_SIZE_GB}GB)"
    echo "   실행: rm -rf ~/.cache/huggingface/*"
    echo "   주의: 모든 모델이 다시 다운로드됩니다"
  else
    echo "✅ 캐시 정리 불필요 (현재: ${CACHE_SIZE_GB}GB)"
  fi
fi

# Docker 정리
DOCKER_SIZE=$(docker system df --format "table {{.Type}}\t{{.Size}}" | grep -E "(Images|Containers|Local Volumes)" | awk '{sum+=$2} END {print sum}' 2>/dev/null || echo "0")
if [ "$DOCKER_SIZE" != "0" ] && [ "$DOCKER_SIZE" -gt 10 ]; then
  echo "🧹 Docker 정리 권장 (현재: ${DOCKER_SIZE}GB)"
  echo "   실행: docker system prune -f"
  echo "   실행: docker image prune -f"
else
  echo "✅ Docker 정리 불필요"
fi

echo ""
echo "💡 정기 점검: 주 1회 실행 권장"
