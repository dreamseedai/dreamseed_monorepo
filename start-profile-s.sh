#!/bin/bash

# 🟢 프로필 S (가장 안정) - 단일 7B 상주
# Mistral-7B-Instruct v0.3 @8000 (가용 모델)

set -e

echo "🚀 프로필 S 시작: Mistral-7B-Instruct v0.3 단독 운영"

# 기존 컨테이너 정리
echo "🧹 기존 컨테이너 정리 중..."
docker stop dreamseed-mistral-7b dreamseed-qwen2-7b dreamseed-phi3-mini 2>/dev/null || true
docker rm dreamseed-mistral-7b dreamseed-qwen2-7b dreamseed-phi3-mini 2>/dev/null || true

# 7B 모델 시작 (Mistral 우선, 실패 시 Qwen2.5)
echo "🤖 Mistral-7B-Instruct v0.3 시작 중..."
docker run --gpus all --pull always --rm -d --name dreamseed-mistral-7b \
  -p 8000:8000 \
  -v $HOME/.cache/huggingface:/root/.cache/huggingface \
  --env HF_HOME=/root/.cache/huggingface \
  --shm-size=2g \
  vllm/vllm-openai:latest \
  --model mistralai/Mistral-7B-Instruct-v0.3 \
  --dtype auto \
  --max-model-len 6144 \
  --max-num-seqs 16 \
  --max-num-batched-tokens 2048 \
  --gpu-memory-utilization 0.82

echo "⏳ 모델 로딩 대기 중... (약 3-5분)"
sleep 60

# 헬스체크
echo "🔍 헬스체크 중..."
for i in {1..20}; do
  if curl -s http://127.0.0.1:8000/v1/models > /dev/null 2>&1; then
    echo "✅ Mistral 모델 준비 완료!"
    # 웜업 호출 (콜드스타트 방지)
    echo "🔥 웜업 호출 중..."
    curl -s http://127.0.0.1:8000/v1/models > /dev/null 2>&1
    break
  fi
  echo "⏳ 대기 중... ($i/20)"
  sleep 15
done

# Mistral 실패 시 Qwen2.5로 폴백
if ! curl -s http://127.0.0.1:8000/v1/models > /dev/null 2>&1; then
  echo "⚠️  Mistral 로딩 실패, Qwen2.5-7B로 폴백..."
  docker stop dreamseed-mistral-7b 2>/dev/null || true
  docker rm dreamseed-mistral-7b 2>/dev/null || true
  
  docker run --gpus all --pull always --rm -d --name dreamseed-qwen2-7b \
    -p 8000:8000 \
    -v $HOME/.cache/huggingface:/root/.cache/huggingface \
    --env HF_HOME=/root/.cache/huggingface \
    --shm-size=2g \
    vllm/vllm-openai:latest \
    --model Qwen/Qwen2.5-7B-Instruct \
    --dtype auto \
    --max-model-len 6144 \
    --max-num-seqs 16 \
    --max-num-batched-tokens 2048 \
    --gpu-memory-utilization 0.82
  
  echo "⏳ Qwen2.5 모델 로딩 대기 중..."
  for i in {1..20}; do
    if curl -s http://127.0.0.1:8000/v1/models > /dev/null 2>&1; then
      echo "✅ Qwen2.5 모델 준비 완료!"
      # 웜업 호출 (콜드스타트 방지)
      echo "🔥 웜업 호출 중..."
      curl -s http://127.0.0.1:8000/v1/models > /dev/null 2>&1
      break
    fi
    echo "⏳ Qwen2.5 대기 중... ($i/20)"
    sleep 15
  done
fi

# 상태 확인
echo "📊 현재 상태:"
echo "컨테이너: $(docker ps --filter name=dreamseed- --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}')"
echo "GPU 메모리:"
nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader,nounits | awk '{printf "  사용: %dMB / %dMB (%.1f%%)\n", $1, $2, ($1/$2)*100}'

echo ""
echo "🎯 프로필 S 설정 완료!"
echo "📍 엔드포인트: http://127.0.0.1:8000"
echo "🔧 라우터: 8001/8002 미기동 시 자동 폴백"
echo "💡 정지: ./stop-profile-s.sh"
