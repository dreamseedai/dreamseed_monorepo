#!/bin/bash
# GPT-4.1 mini batch MathML 변환 실행 스크립트

set -euo pipefail

# 설정
BATCH_SIZE=${1:-100}
TOTAL_LIMIT=${2:-1000}
LOG_FILE="batch_conversion_$(date +%Y%m%d_%H%M%S).log"

echo "=== GPT-4.1 mini batch MathML 변환 시작 ==="
echo "배치 크기: $BATCH_SIZE"
echo "총 처리량: $TOTAL_LIMIT"
echo "로그 파일: $LOG_FILE"

# API 키 확인
if [ -z "${OPENAI_API_KEY:-}" ]; then
    echo "❌ OPENAI_API_KEY 환경변수가 설정되지 않았습니다."
    echo "다음 명령어로 설정하세요:"
    echo "export OPENAI_API_KEY='your-api-key-here'"
    exit 1
fi

# Python 의존성 확인
echo "Python 의존성 확인 중..."
python3 -c "import aiohttp, asyncio" 2>/dev/null || {
    echo "필요한 Python 패키지 설치 중..."
    pip3 install aiohttp
}

# 배치 변환 실행
echo "배치 변환 시작..."
python3 batch_mathml_processor.py 2>&1 | tee "$LOG_FILE"

echo "=== 배치 변환 완료 ==="
echo "결과 파일들:"
ls -la conversion_results_batch_*.json 2>/dev/null || echo "결과 파일이 없습니다."

echo "로그 파일: $LOG_FILE"
