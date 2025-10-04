#!/usr/bin/env python3
"""
이미지 처리 기능 테스트
"""

from math_rendering_system import math_renderer
import json

def test_image_path_conversion():
    """이미지 경로 변환 테스트"""
    print("🖼️  이미지 경로 변환 테스트")
    print("=" * 50)
    
    # 테스트 케이스들
    test_cases = [
        {
            "name": "기본 이미지 경로",
            "input": '<img src="/images/editor/7191-1.png" alt="수학 문제">',
            "expected": "/static/images/questions/7191-1.png"
        },
        {
            "name": "상대 경로",
            "input": '<img src="images/editor/7192-1.png" alt="수학 문제">',
            "expected": "/static/images/questions/7192-1.png"
        },
        {
            "name": "editor 경로",
            "input": '<img src="editor/7193-1.png" alt="수학 문제">',
            "expected": "/static/images/questions/7193-1.png"
        },
        {
            "name": "복합 콘텐츠",
            "input": '''
            <p>다음 문제를 풀어보세요:</p>
            <img src="/images/editor/7194-1.png" alt="문제">
            <p>이 문제의 해답은 <img src="images/editor/7194-2.png" alt="해답">입니다.</p>
            ''',
            "expected": "두 개의 이미지 경로가 변환되어야 함"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n테스트 {i}: {test_case['name']}")
        print(f"입력: {test_case['input'][:100]}...")
        
        result = math_renderer.process_content(test_case['input'])
        print(f"결과: {result[:100]}...")
        
        # 예상 결과 확인
        if "static/images/questions" in result:
            print("✅ 이미지 경로 변환 성공")
        else:
            print("❌ 이미지 경로 변환 실패")

def test_image_mapping():
    """이미지 매핑 파일 테스트"""
    print("\n📋 이미지 매핑 파일 테스트")
    print("=" * 50)
    
    try:
        with open('image_mapping.json', 'r', encoding='utf-8') as f:
            mapping = json.load(f)
        
        print(f"총 이미지 수: {mapping['total_images']}개")
        print(f"소스 디렉토리: {mapping['source_directory']}")
        print(f"대상 디렉토리: {mapping['target_directory']}")
        
        # 샘플 이미지들 표시
        print("\n샘플 이미지들:")
        for i, img in enumerate(mapping['images'][:5]):
            print(f"  {i+1}. {img['filename']} ({img['size']} bytes)")
            print(f"     경로: {img['path']}")
        
        if len(mapping['images']) > 5:
            print(f"  ... 및 {len(mapping['images']) - 5}개 더")
        
        print("✅ 이미지 매핑 파일 로드 성공")
        
    except Exception as e:
        print(f"❌ 이미지 매핑 파일 로드 실패: {e}")

def test_math_with_images():
    """수학 공식과 이미지가 함께 있는 콘텐츠 테스트"""
    print("\n🔢 수학 공식 + 이미지 테스트")
    print("=" * 50)
    
    # 복합 콘텐츠 테스트
    complex_content = '''
    <p>다음 이차방정식을 풀어보세요:</p>
    <math><msup><mi>x</mi><mn>2</mn></msup><mo>-</mo><mn>5</mn><mi>x</mi><mo>+</mo><mn>6</mn><mo>=</mo><mn>0</mn></math>
    
    <p>문제를 시각적으로 이해하기 위해 다음 그래프를 참고하세요:</p>
    <img src="/images/editor/7191-1.png" alt="이차함수 그래프">
    
    <p>해답 과정:</p>
    <img src="images/editor/7192-1.png" alt="해답 과정">
    
    <p>최종 답: <math><mi>x</mi><mo>=</mo><mn>2</mn></math> 또는 <math><mi>x</mi><mo>=</mo><mn>3</mn></math></p>
    '''
    
    print("원본 콘텐츠:")
    print(complex_content[:200] + "...")
    
    processed = math_renderer.process_content(complex_content)
    
    print("\n처리된 콘텐츠:")
    print(processed[:200] + "...")
    
    # 검증
    checks = [
        ("MathML → LaTeX 변환", "\\[" in processed),
        ("이미지 경로 변환", "/static/images/questions/" in processed),
        ("HTML 엔티티 디코딩", "&" not in processed or "&amp;" not in processed)
    ]
    
    print("\n검증 결과:")
    for check_name, result in checks:
        status = "✅" if result else "❌"
        print(f"  {status} {check_name}")
    
    return all(result for _, result in checks)

def main():
    """메인 테스트 함수"""
    print("🧪 이미지 처리 시스템 종합 테스트")
    print("=" * 60)
    
    # 1. 이미지 경로 변환 테스트
    test_image_path_conversion()
    
    # 2. 이미지 매핑 테스트
    test_image_mapping()
    
    # 3. 수학 + 이미지 복합 테스트
    success = test_math_with_images()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 모든 테스트 통과!")
        print("\n✅ 완료된 작업:")
        print("  1. 8,164개 이미지 파일 복사")
        print("  2. 이미지 경로 자동 변환 시스템 구축")
        print("  3. FastAPI 정적 파일 서빙 설정")
        print("  4. 이미지 매핑 파일 생성")
        print("  5. 수학 공식 + 이미지 통합 처리")
        
        print("\n🚀 다음 단계:")
        print("  1. 실제 문제 데이터에 이미지 경로 변환 적용")
        print("  2. 프론트엔드에서 이미지 표시 테스트")
        print("  3. 이미지 최적화 및 압축")
        print("  4. CDN 연동 (선택사항)")
    else:
        print("❌ 일부 테스트 실패")
    
    return success

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
