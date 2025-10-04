#!/bin/bash

# MathML 변환 품질 검증 도구 실행 스크립트
# DreamSeed AI 프로젝트

echo "🔬 MathML 변환 품질 검증 도구 시작"
echo "================================================"

# 가상환경 활성화 (있는 경우)
if [ -d "venv" ]; then
    echo "📦 가상환경 활성화 중..."
    source venv/bin/activate
fi

# 필요한 패키지 설치
echo "📦 필요한 패키지 설치 중..."
pip install flask flask-cors

# 검증 도구 실행
echo "🚀 검증 도구 실행 중..."
echo "📱 웹 브라우저에서 http://localhost:5000 접속"
echo ""

python3 validation_api.py
