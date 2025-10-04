#!/usr/bin/env python3
"""
수학 홈페이지 API 테스트
"""

import requests
import json
import time

def test_math_homepage_api():
    """수학 홈페이지 API 테스트"""
    print("🧮 수학 홈페이지 API 테스트")
    print("=" * 50)
    
    base_url = "http://localhost:8001"
    
    # 1. 홈페이지 접근 테스트
    print("\n1. 홈페이지 접근 테스트")
    try:
        response = requests.get(f"{base_url}/", timeout=5)
        if response.status_code == 200:
            print("✅ 홈페이지 접근 성공")
            print(f"   - 응답 크기: {len(response.text)} bytes")
            print(f"   - HTML 포함: {'<html>' in response.text}")
        else:
            print(f"❌ 홈페이지 접근 실패: {response.status_code}")
    except Exception as e:
        print(f"❌ 홈페이지 접근 오류: {e}")
    
    # 2. 카테고리 조회 테스트
    print("\n2. 카테고리 조회 테스트")
    test_grades = ["G06", "G09", "G12", "SAT", "AP"]
    
    for grade in test_grades:
        try:
            response = requests.get(f"{base_url}/api/math/categories?grade={grade}", timeout=5)
            if response.status_code == 200:
                categories = response.json()
                print(f"✅ {grade} 카테고리 조회 성공: {len(categories)}개")
                for cat in categories[:2]:  # 처음 2개만 표시
                    print(f"   - {cat['category_name']} ({cat['question_count']}문제)")
            else:
                print(f"❌ {grade} 카테고리 조회 실패: {response.status_code}")
        except Exception as e:
            print(f"❌ {grade} 카테고리 조회 오류: {e}")
    
    # 3. 문제 목록 조회 테스트
    print("\n3. 문제 목록 조회 테스트")
    try:
        response = requests.get(f"{base_url}/api/math/questions?grade=G09&category_id=G09M001", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 문제 목록 조회 성공: {data['total_count']}개")
            print(f"   - 필터: {data['filters']}")
            for q in data['questions'][:2]:  # 처음 2개만 표시
                print(f"   - {q['title']} ({q['difficulty']})")
        else:
            print(f"❌ 문제 목록 조회 실패: {response.status_code}")
    except Exception as e:
        print(f"❌ 문제 목록 조회 오류: {e}")
    
    # 4. 키워드 검색 테스트
    print("\n4. 키워드 검색 테스트")
    try:
        response = requests.get(f"{base_url}/api/math/questions?grade=G09&keyword=quadratic", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 키워드 검색 성공: {data['total_count']}개")
            for q in data['questions']:
                print(f"   - {q['title']}")
        else:
            print(f"❌ 키워드 검색 실패: {response.status_code}")
    except Exception as e:
        print(f"❌ 키워드 검색 오류: {e}")
    
    # 5. 시퀀스 ID 검색 테스트
    print("\n5. 시퀀스 ID 검색 테스트")
    try:
        response = requests.get(f"{base_url}/api/math/questions?grade=G09&sequence_id=Q001", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 시퀀스 ID 검색 성공: {data['total_count']}개")
            for q in data['questions']:
                print(f"   - {q['title']} (ID: {q['question_id']})")
        else:
            print(f"❌ 시퀀스 ID 검색 실패: {response.status_code}")
    except Exception as e:
        print(f"❌ 시퀀스 ID 검색 오류: {e}")
    
    # 6. 특정 문제 조회 테스트
    print("\n6. 특정 문제 조회 테스트")
    try:
        response = requests.get(f"{base_url}/api/math/question/Q001", timeout=5)
        if response.status_code == 200:
            question = response.json()
            print(f"✅ 특정 문제 조회 성공: {question['title']}")
            print(f"   - 카테고리: {question['category']}")
            print(f"   - 난이도: {question['difficulty']}")
            print(f"   - 내용 길이: {len(question['content'])} chars")
        else:
            print(f"❌ 특정 문제 조회 실패: {response.status_code}")
    except Exception as e:
        print(f"❌ 특정 문제 조회 오류: {e}")

def test_error_handling():
    """에러 처리 테스트"""
    print("\n🚨 에러 처리 테스트")
    print("=" * 50)
    
    base_url = "http://localhost:8001"
    
    # 1. 잘못된 과목 테스트
    print("\n1. 잘못된 과목 테스트 (Physics)")
    try:
        response = requests.get(f"{base_url}/api/math/categories?grade=G09&subject=P", timeout=5)
        if response.status_code == 400:
            print("✅ 잘못된 과목 에러 처리 성공")
            print(f"   - 에러 메시지: {response.json()['detail']}")
        else:
            print(f"❌ 잘못된 과목 에러 처리 실패: {response.status_code}")
    except Exception as e:
        print(f"❌ 잘못된 과목 에러 처리 오류: {e}")
    
    # 2. 존재하지 않는 학년 테스트
    print("\n2. 존재하지 않는 학년 테스트")
    try:
        response = requests.get(f"{base_url}/api/math/categories?grade=G99", timeout=5)
        if response.status_code == 404:
            print("✅ 존재하지 않는 학년 에러 처리 성공")
            print(f"   - 에러 메시지: {response.json()['detail']}")
        else:
            print(f"❌ 존재하지 않는 학년 에러 처리 실패: {response.status_code}")
    except Exception as e:
        print(f"❌ 존재하지 않는 학년 에러 처리 오류: {e}")

def main():
    """메인 테스트 함수"""
    print("🧪 수학 홈페이지 API 종합 테스트")
    print("=" * 60)
    
    # 서버 시작 대기
    print("서버 시작 대기 중...")
    time.sleep(2)
    
    # 기본 기능 테스트
    test_math_homepage_api()
    
    # 에러 처리 테스트
    test_error_handling()
    
    print("\n" + "=" * 60)
    print("🎉 수학 홈페이지 API 테스트 완료!")
    print("\n✅ 구현된 기능:")
    print("  1. 수학 전용 홈페이지 (HTML)")
    print("  2. 학년별 카테고리 조회")
    print("  3. 문제 목록 조회 (필터링 지원)")
    print("  4. 키워드 검색")
    print("  5. 시퀀스 ID 검색")
    print("  6. 특정 문제 조회")
    print("  7. 에러 처리")
    
    print("\n🚀 다음 단계:")
    print("  1. 실제 데이터베이스 연동")
    print("  2. 문제 표시 페이지 구현")
    print("  3. 사용자 세션 관리")
    print("  4. 즐겨찾기 기능")
    print("  5. 학습 진행률 추적")

if __name__ == "__main__":
    main()
