#!/bin/bash

# DreamSeedAI Auto Mode 중지 스크립트

echo "🛑 DreamSeedAI Auto Mode 중지..."

# Docker 컨테이너 중지
echo "📚 기본 모델 중지..."
docker stop dreamseed-llama 2>/dev/null || echo "기본 모델이 실행 중이 아닙니다."

echo "💻 코딩 모델 중지..."
docker stop dreamseed-coder 2>/dev/null || echo "코딩 모델이 실행 중이 아닙니다."

echo "⚡ 경량 모델 중지..."
docker stop dreamseed-fast 2>/dev/null || echo "경량 모델이 실행 중이 아닙니다."

# FastAPI 라우터 중지
echo "🧠 Auto 라우터 중지..."
pkill -f "uvicorn router:app" 2>/dev/null || echo "라우터가 실행 중이 아닙니다."

echo "✅ DreamSeedAI Auto Mode 중지 완료!"
