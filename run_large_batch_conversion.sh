#!/usr/bin/env bash
# 대용량 MathML 변환 실행 스크립트

# 스크립트가 위치한 디렉토리로 이동
SCRIPT_DIR=$(dirname "$(readlink -f "$0")")
cd "$SCRIPT_DIR" || exit

echo "🚀 대용량 GPT-4.1 mini batch 변환 시스템을 시작합니다..."

# Python 가상 환경 활성화 (필요시)
# if [ -d ".venv" ]; then
#   source .venv/bin/activate
# fi

# OpenAI API 키 환경 변수 확인
if [ -z "$OPENAI_API_KEY" ]; then
  echo "⚠️ OPENAI_API_KEY 환경 변수가 설정되지 않았습니다."
  echo "   API 키 없이 Mock 테스트 모드로 실행됩니다."
  echo "   실제 변환을 위해서는 'export OPENAI_API_KEY=\"YOUR_API_KEY\"'를 실행해주세요."
fi

# 데이터베이스 URL 설정 (필요시)
if [ -z "$DATABASE_URL" ]; then
  echo "⚠️ DATABASE_URL 환경 변수가 설정되지 않았습니다."
  echo "   기본값 사용: postgresql://user:password@localhost/dreamseed"
fi

# 배치 크기 설정 (기본값: 100)
BATCH_SIZE=${1:-100}

# 총 처리할 항목 수 설정 (기본값: 1000)
TOTAL_ITEMS=${2:-1000}

echo "📊 설정:"
echo "   - 배치 크기: $BATCH_SIZE"
echo "   - 총 처리 항목: $TOTAL_ITEMS"
echo "   - API 키: ${OPENAI_API_KEY:+설정됨}"
echo "   - 데이터베이스: ${DATABASE_URL:-기본값}"

# Python 스크립트 실행
python3 -c "
import asyncio
import os
from batch_mathml_processor import BatchMathMLProcessor

async def main():
    # API 키 확인
    api_key = os.getenv('OPENAI_API_KEY', 'test-key')
    
    # 프로세서 생성
    processor = BatchMathMLProcessor(api_key, batch_size=$BATCH_SIZE)
    
    # 전체 변환 실행
    await processor.run_full_conversion(total_limit=$TOTAL_ITEMS)

# 실행
asyncio.run(main())
"

# 가상 환경 비활성화 (필요시)
# if [ -d ".venv" ]; then
#   deactivate
# fi

echo "✅ 대용량 배치 변환 시스템 실행 완료."
echo "   결과는 'conversion_results_batch_*.json' 파일에 저장됩니다."
echo "   진행 상황은 로그에서 확인할 수 있습니다."
