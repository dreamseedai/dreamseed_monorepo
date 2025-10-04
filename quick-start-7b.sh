#!/bin/bash

# 🔵 프로필 O - 온디맨드 7B 코더 빠른 시작
# 코딩 요청이 많을 때만 실행

set -e

echo "🔵 온디맨드 7B 코더 시작"

# 환경변수 설정
export HF_TOKEN=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

# 기존 7B 컨테이너 정리
echo "🧹 기존 7B 컨테이너 정리 중..."
docker stop dreamseed-qwen-7b 2>/dev/null || true
docker rm dreamseed-qwen-7b 2>/dev/null || true

# 7B 코더 시작
echo "🤖 Qwen2.5-Coder-7B-Instruct 시작 중..."
docker run --gpus all --pull always --rm -d --name dreamseed-qwen-7b \
  -e HF_TOKEN=$HF_TOKEN \
  -p 8001:8001 \
  -v $HOME/.cache/huggingface:/root/.cache/huggingface \
  --env HF_HOME=/root/.cache/huggingface \
  --shm-size=2g \
  vllm/vllm-openai:latest \
  --model Qwen/Qwen2.5-Coder-7B-Instruct \
  --dtype auto \
  --max-model-len 6144 \
  --max-num-seqs 16 \
  --max-num-batched-tokens 2048 \
  --gpu-memory-utilization 0.82 \
  --port 8001

echo "⏳ 7B 코더 로딩 대기 중... (약 2-3분)"
sleep 30

# 헬스체크
echo "🔍 7B 코더 헬스체크 중..."
for i in {1..12}; do
  if curl -s http://127.0.0.1:8001/v1/models > /dev/null 2>&1; then
    echo "✅ 7B 코더 준비 완료!"
    # 웜업 호출 (콜드스타트 방지)
    echo "🔥 웜업 호출 중..."
    curl -s http://127.0.0.1:8001/v1/models > /dev/null 2>&1
    break
  fi
  echo "⏳ 7B 코더 대기 중... ($i/12)"
  sleep 10
done

# 상태 확인
echo "📊 현재 상태:"
echo "컨테이너:"
docker ps --filter name=dreamseed- --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
echo "GPU 메모리:"
nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader,nounits | awk '{printf "  사용: %dMB / %dMB (%.1f%%)\n", $1, $2, ($1/$2)*100}'

echo ""
echo "🎯 온디맨드 7B 코더 설정 완료!"
echo "📍 7B 코딩: http://127.0.0.1:8001"
echo "🔧 라우터: 자동 분기 (코딩 → 7B, 일반 → 8B)"
echo "💡 정지: docker stop dreamseed-qwen-7b"
