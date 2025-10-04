#!/bin/bash

# OpenAI API 키 설정 스크립트

echo "=========================================="
echo "OpenAI API 키 설정"
echo "=========================================="
echo

# 현재 API 키 상태 확인
if [ -n "$OPENAI_API_KEY" ]; then
    echo "✅ API 키가 이미 설정되어 있습니다: ${OPENAI_API_KEY:0:8}...${OPENAI_API_KEY: -4}"
    echo
    echo "테스트를 실행하시겠습니까? (y/n)"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        echo "실제 AI 변환 테스트를 실행합니다..."
        source mathml_env/bin/activate
        python3 real_ai_mathml_converter.py
    fi
    exit 0
fi

echo "API 키를 설정하는 방법을 선택하세요:"
echo "1) 환경변수로 설정 (현재 세션만)"
echo "2) .env 파일로 설정 (영구적)"
echo "3) 직접 입력"
echo
read -p "선택 (1-3): " choice

case $choice in
    1)
        echo
        echo "API 키를 입력하세요:"
        read -s api_key
        export OPENAI_API_KEY="$api_key"
        echo
        echo "✅ API 키가 현재 세션에 설정되었습니다."
        echo
        echo "테스트를 실행하시겠습니까? (y/n)"
        read -r response
        if [[ "$response" =~ ^[Yy]$ ]]; then
            source mathml_env/bin/activate
            python3 real_ai_mathml_converter.py
        fi
        ;;
    2)
        echo
        echo "API 키를 입력하세요:"
        read -s api_key
        echo "OPENAI_API_KEY=$api_key" > .env
        echo
        echo "✅ API 키가 .env 파일에 저장되었습니다."
        echo "다음 명령어로 테스트를 실행하세요:"
        echo "  source mathml_env/bin/activate"
        echo "  python3 real_ai_mathml_converter.py"
        ;;
    3)
        echo
        echo "API 키를 입력하세요:"
        read -s api_key
        echo
        echo "다음 명령어로 API 키를 설정하고 테스트를 실행하세요:"
        echo "  export OPENAI_API_KEY='$api_key'"
        echo "  source mathml_env/bin/activate"
        echo "  python3 real_ai_mathml_converter.py"
        ;;
    *)
        echo "잘못된 선택입니다."
        exit 1
        ;;
esac

echo
echo "보안 주의사항:"
echo "- API 키를 코드에 직접 입력하지 마세요"
echo "- API 키를 공유하지 마세요"
echo "- .env 파일은 이미 .gitignore에 포함되어 있습니다"
