#!/usr/bin/env python3
"""
OpenAI API 키 설정 및 테스트 스크립트
"""

import os
import sys
from pathlib import Path


def setup_api_key():
    """API 키 설정을 위한 안내"""
    print("=" * 60)
    print("OpenAI API 키 설정")
    print("=" * 60)
    print()
    print("다음 중 하나의 방법으로 API 키를 설정하세요:")
    print()
    print("방법 1: 환경변수로 설정 (권장)")
    print("  export OPENAI_API_KEY='your-api-key-here'")
    print()
    print("방법 2: .env 파일 생성")
    print("  echo 'OPENAI_API_KEY=your-api-key-here' > .env")
    print()
    print("방법 3: 직접 입력 (보안상 권장하지 않음)")
    print("  python3 -c \"import os; os.environ['OPENAI_API_KEY'] = 'your-key'\"")
    print()

    # 현재 API 키 상태 확인
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        print(f"✅ API 키가 설정되어 있습니다: {api_key[:8]}...{api_key[-4:]}")
        return True
    else:
        print("❌ API 키가 설정되어 있지 않습니다.")
        return False


def test_api_connection():
    """API 연결 테스트"""
    try:
        from ai_client import get_model, get_openai_client

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("❌ API 키가 설정되지 않았습니다.")
            return False

        # OpenAI 클라이언트 초기화 (OPENAI_BASE_URL 및 로컬 토글 지원)
        client = get_openai_client(api_key)

        print("🔄 OpenAI API 연결 테스트 중...")

        # 간단한 테스트 요청
        response = client.chat.completions.create(
            model=get_model(),
            messages=[
                {
                    "role": "user",
                    "content": "Hello! This is a test message. Please respond with 'API connection successful!'",
                }
            ],
            max_tokens=50,
        )

        print("✅ API 연결 성공!")
        print(f"응답: {response.choices[0].message.content}")
        return True

    except ImportError:
        print("❌ OpenAI 라이브러리가 설치되지 않았습니다.")
        print("다음 명령어로 설치하세요: pip install openai")
        return False
    except Exception as e:
        print(f"❌ API 연결 실패: {str(e)}")
        return False


def main():
    """메인 함수"""
    print("OpenAI API 설정 및 테스트")
    print()

    # API 키 설정 상태 확인
    if not setup_api_key():
        print()
        print("API 키를 설정한 후 다시 실행해주세요.")
        return

    print()

    # API 연결 테스트
    if test_api_connection():
        print()
        print("🎉 모든 설정이 완료되었습니다!")
        print("이제 AI MathML 변환을 테스트할 수 있습니다.")
    else:
        print()
        print("❌ API 설정에 문제가 있습니다.")
        print("API 키와 네트워크 연결을 확인해주세요.")


if __name__ == "__main__":
    main()
