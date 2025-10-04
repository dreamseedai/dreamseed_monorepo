#!/bin/bash

# MathML to MathJax + ChemDoodle 변환 실행 스크립트
# DreamSeed AI 프로젝트

echo "🚀 MathML to MathJax + ChemDoodle 변환 시작"
echo "================================================"

# 가상환경 활성화 (있는 경우)
if [ -d "venv" ]; then
    echo "📦 가상환경 활성화 중..."
    source venv/bin/activate
fi

# 환경 변수 설정
export DATABASE_URL="${DATABASE_URL:-postgresql://postgres:password@localhost:5432/dreamseed}"

# API 키 설정 (필요한 경우)
export OPENAI_API_KEY="${OPENAI_API_KEY:-}"

# 변환 파라미터
BATCH_SIZE=${1:-100}
TOTAL_LIMIT=${2:-1000}
OUTPUT_FILE=${3:-"mathml_conversion_results.jsonl"}

echo "📋 변환 설정:"
echo "  - 배치 크기: $BATCH_SIZE"
echo "  - 총 제한: $TOTAL_LIMIT"
echo "  - 출력 파일: $OUTPUT_FILE"
echo "  - 데이터베이스: $DATABASE_URL"
echo ""

# 기존 결과 파일 백업
if [ -f "$OUTPUT_FILE" ]; then
    echo "📁 기존 결과 파일 백업 중..."
    cp "$OUTPUT_FILE" "${OUTPUT_FILE}.backup.$(date +%Y%m%d_%H%M%S)"
fi

# 변환 실행
echo "🔄 변환 실행 중..."
python3 mathml_to_mathjax_chemdoodle_converter.py

# 결과 확인
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ 변환 완료!"
    echo "📊 결과 파일: $OUTPUT_FILE"
    
    # 결과 통계 출력
    if [ -f "$OUTPUT_FILE" ]; then
        TOTAL_LINES=$(wc -l < "$OUTPUT_FILE")
        echo "📈 총 변환된 항목: $TOTAL_LINES개"
        
        # 성공/실패 통계
        SUCCESS_COUNT=$(grep '"success": true' "$OUTPUT_FILE" | wc -l)
        ERROR_COUNT=$(grep '"success": false' "$OUTPUT_FILE" | wc -l)
        
        echo "✅ 성공: $SUCCESS_COUNT개"
        echo "❌ 실패: $ERROR_COUNT개"
        
        # 변환 타입별 통계
        MATHJAX_COUNT=$(grep '"conversion_type": "mathjax"' "$OUTPUT_FILE" | wc -l)
        CHEMDOODLE_COUNT=$(grep '"conversion_type": "chemdoodle"' "$OUTPUT_FILE" | wc -l)
        HYBRID_COUNT=$(grep '"conversion_type": "hybrid"' "$OUTPUT_FILE" | wc -l)
        
        echo "📐 MathJax: $MATHJAX_COUNT개"
        echo "🧪 ChemDoodle: $CHEMDOODLE_COUNT개"
        echo "🔄 하이브리드: $HYBRID_COUNT개"
    fi
else
    echo "❌ 변환 실패!"
    exit 1
fi

echo ""
echo "🎯 변환 작업 완료!"
echo "================================================"
