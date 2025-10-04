#!/bin/bash

# DreamSeedAI Auto Mode 시작 스크립트
# RTX 5090 + vLLM + FastAPI 라우터

echo "🚀 DreamSeedAI Auto Mode 시작..."

# HuggingFace 토큰 확인
if [ -z "$HF_TOKEN" ]; then
    echo "❌ HF_TOKEN이 설정되지 않았습니다."
    echo "export HF_TOKEN=<your_hf_token> 을 먼저 실행해주세요."
    exit 1
fi

echo "✅ HF_TOKEN 설정됨"

# 1. 기본 모델 (Llama 3 8B Instruct) @8000
echo "📚 기본 모델 시작 (Llama 3 8B @8000)..."
docker run --gpus all --pull always --rm -d --name dreamseed-llama \
  -e HF_TOKEN=$HF_TOKEN \
  -p 8000:8000 \
  -v $HOME/.cache/huggingface:/root/.cache/huggingface \
  --shm-size=2g \
  vllm/vllm-openai:latest \
  --model meta-llama/Meta-Llama-3-8B-Instruct \
  --dtype auto \
  --max-model-len 8192 \
  --gpu-memory-utilization 0.9 \
  --tensor-parallel-size 1

# 2. 코딩 특화 모델 (Qwen2.5-Coder 7B) @8001
echo "💻 코딩 모델 시작 (Qwen2.5-Coder 7B @8001)..."
docker run --gpus all --rm -d --name dreamseed-coder \
  -e HF_TOKEN=$HF_TOKEN \
  -p 8001:8001 \
  -v $HOME/.cache/huggingface:/root/.cache/huggingface \
  --shm-size=2g \
  vllm/vllm-openai:latest \
  --model Qwen/Qwen2.5-Coder-7B-Instruct \
  --dtype auto \
  --max-model-len 8192 \
  --gpu-memory-utilization 0.9 \
  --port 8001

# 3. 경량 모델 (Mistral 7B) @8002
echo "⚡ 경량 모델 시작 (Mistral 7B @8002)..."
docker run --gpus all --rm -d --name dreamseed-fast \
  -e HF_TOKEN=$HF_TOKEN \
  -p 8002:8002 \
  -v $HOME/.cache/huggingface:/root/.cache/huggingface \
  --shm-size=2g \
  vllm/vllm-openai:latest \
  --model mistralai/Mistral-7B-Instruct-v0.3 \
  --dtype auto \
  --max-model-len 8192 \
  --gpu-memory-utilization 0.9 \
  --port 8002

# 잠시 대기 (모델 로딩)
echo "⏳ 모델 로딩 대기 중..."
sleep 30

# 웜업 (콜드스타트 방지)
echo "🔥 모델 웜업 중..."
curl -s http://127.0.0.1:8000/v1/models > /dev/null || echo "기본 모델 웜업 실패"
curl -s http://127.0.0.1:8001/v1/models > /dev/null || echo "코딩 모델 웜업 실패"
curl -s http://127.0.0.1:8002/v1/models > /dev/null || echo "경량 모델 웜업 실패"

# 4. Auto 라우터 시작 @8010
echo "🧠 Auto 라우터 시작 (FastAPI @8010)..."
cd /home/won/projects/dreamseed_monorepo
uvicorn router:app --host 127.0.0.1 --port 8010 --reload &

echo "✅ DreamSeedAI Auto Mode 시작 완료!"
echo ""
echo "📊 서비스 상태:"
echo "  - 기본 모델 (Llama 3 8B): http://127.0.0.1:8000"
echo "  - 코딩 모델 (Qwen2.5-Coder): http://127.0.0.1:8001"
echo "  - 경량 모델 (Mistral 7B): http://127.0.0.1:8002"
echo "  - Auto 라우터: http://127.0.0.1:8010"
echo ""
echo "🔌 Cursor MCP 등록:"
echo "  OPENAI_BASE_URL: http://127.0.0.1:8010/v1"
echo "  OPENAI_API_KEY: dummy"
echo ""
echo "🧪 테스트:"
echo "  curl http://127.0.0.1:8010/health"
echo "  curl http://127.0.0.1:8010/models"
