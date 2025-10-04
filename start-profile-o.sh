#!/bin/bash

# 🔵 프로필 O (권장) - 온디맨드 7B 부팅
# 기본: 8B 단독 + 필요시 7B 코더 추가

set -e

echo "🔵 프로필 O 시작: 온디맨드 7B 부팅"

# 환경변수 설정
export HF_TOKEN=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

# 기존 컨테이너 정리
echo "🧹 기존 컨테이너 정리 중..."
docker stop dreamseed-llama-8b dreamseed-qwen-7b 2>/dev/null || true
docker rm dreamseed-llama-8b dreamseed-qwen-7b 2>/dev/null || true

# 8B 모델 시작 (기본)
echo "🤖 Llama-3.1-8B-Instruct 시작 중..."
docker run --gpus all --pull always --rm -d --name dreamseed-llama-8b \
  -e HF_TOKEN=$HF_TOKEN \
  -p 8000:8000 \
  -v $HOME/.cache/huggingface:/root/.cache/huggingface \
  --shm-size=2g \
  vllm/vllm-openai:latest \
  --model meta-llama/Llama-3.1-8B-Instruct \
  --dtype auto \
  --max-model-len 6144 \
  --gpu-memory-utilization 0.85 \
  --tensor-parallel-size 1

echo "⏳ 8B 모델 로딩 대기 중... (약 2-3분)"
sleep 30

# 8B 헬스체크
echo "🔍 8B 모델 헬스체크 중..."
for i in {1..12}; do
  if curl -s http://127.0.0.1:8000/v1/models > /dev/null 2>&1; then
    echo "✅ 8B 모델 준비 완료!"
    break
  fi
  echo "⏳ 8B 모델 대기 중... ($i/12)"
  sleep 10
done

# 7B 코더 시작 (온디맨드)
echo "🤖 Qwen2.5-Coder-7B-Instruct 시작 중..."
docker run --gpus all --pull always --rm -d --name dreamseed-qwen-7b \
  -e HF_TOKEN=$HF_TOKEN \
  -p 8001:8001 \
  -v $HOME/.cache/huggingface:/root/.cache/huggingface \
  --shm-size=2g \
  vllm/vllm-openai:latest \
  --model Qwen/Qwen2.5-Coder-7B-Instruct \
  --dtype auto \
  --max-model-len 6144 \
  --gpu-memory-utilization 0.85 \
  --port 8001

echo "⏳ 7B 코더 로딩 대기 중... (약 2-3분)"
sleep 30

# 7B 헬스체크
echo "🔍 7B 코더 헬스체크 중..."
for i in {1..12}; do
  if curl -s http://127.0.0.1:8001/v1/models > /dev/null 2>&1; then
    echo "✅ 7B 코더 준비 완료!"
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
echo "🎯 프로필 O 설정 완료!"
echo "📍 8B 일반: http://127.0.0.1:8000"
echo "📍 7B 코딩: http://127.0.0.1:8001"
echo "🔧 라우터: 자동 분기 (코딩 → 7B, 일반 → 8B)"
echo "💡 정지: ./stop-profile-o.sh"
echo "💡 7B만 정지: docker stop dreamseed-qwen-7b"
