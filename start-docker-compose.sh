#!/bin/bash

# DreamSeedAI Docker Compose 시작 스크립트

echo "🚀 DreamSeedAI Docker Compose 시작..."

# HuggingFace 토큰 확인
if [ -z "$HF_TOKEN" ]; then
    echo "❌ HF_TOKEN이 설정되지 않았습니다."
    echo "export HF_TOKEN=<your_hf_token> 을 먼저 실행해주세요."
    exit 1
fi

echo "✅ HF_TOKEN 설정됨"

# Docker Compose 시작
echo "🐳 Docker Compose로 모든 서비스 시작..."
docker compose up -d

echo "⏳ 서비스 시작 대기 중..."
sleep 60

# 웜업
echo "🔥 모델 웜업 중..."
curl -s http://127.0.0.1:8000/v1/models > /dev/null || echo "기본 모델 웜업 실패"
curl -s http://127.0.0.1:8001/v1/models > /dev/null || echo "코딩 모델 웜업 실패"
curl -s http://127.0.0.1:8002/v1/models > /dev/null || echo "경량 모델 웜업 실패"

echo "✅ DreamSeedAI Docker Compose 시작 완료!"
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
echo "  ./test-dreamseed-ai.sh"
echo ""
echo "🛑 중지:"
echo "  docker compose down"
