#!/usr/bin/env python3
"""
MathML 변환 테스트 스크립트
DreamSeed AI 프로젝트용 변환기 테스트
"""

import os
import sys
import json
from mathml_to_mathjax_chemdoodle_converter import MathMLConverter

def test_mathml_conversion():
    """MathML 변환 테스트"""
    
    # 테스트용 MathML 샘플들
    test_samples = [
        {
            "name": "기본 수학 수식",
            "mathml": '<math xmlns="http://www.w3.org/1998/Math/MathML"><mfrac><mn>1</mn><mn>2</mn></mfrac></math>',
            "expected_type": "mathjax"
        },
        {
            "name": "화학 반응식",
            "mathml": '<math xmlns="http://www.w3.org/1998/Math/MathML"><mi>H</mi><msub><mn>2</mn></msub><mi>O</mi></math>',
            "expected_type": "chemdoodle"
        },
        {
            "name": "벤젠 고리",
            "mathml": '<math xmlns="http://www.w3.org/1998/Math/MathML"><mtext>벤젠</mtext><mi>C</mi><msub><mn>6</mn></msub><mi>H</mi><msub><mn>6</mn></msub></math>',
            "expected_type": "chemdoodle"
        },
        {
            "name": "복잡한 수학",
            "mathml": '<math xmlns="http://www.w3.org/1998/Math/MathML"><msubsup><mo>∫</mo><mn>0</mn><mn>1</mn></msubsup><msup><mi>x</mi><mn>2</mn></msup><mi>dx</mi></math>',
            "expected_type": "mathjax"
        },
        {
            "name": "화학 평형",
            "mathml": '<math xmlns="http://www.w3.org/1998/Math/MathML"><mi>HA</mi><mo>+</mo><mi>H</mi><msub><mn>2</mn></msub><mi>O</mi><mo>⇌</mo><mi>H</mi><msub><mn>3</mn></msub><msup><mi>O</mi><mo>+</mo></msup><mo>+</mo><mi>A</mi><msup><mo>-</mo></msup></math>',
            "expected_type": "chemdoodle"
        }
    ]
    
    print("🧪 MathML 변환 테스트 시작")
    print("=" * 50)
    
    # 변환기 초기화 (데이터베이스 연결 없이)
    converter = MathMLConverter("dummy_url")
    
    results = []
    
    for i, sample in enumerate(test_samples, 1):
        print(f"\n📝 테스트 {i}: {sample['name']}")
        print(f"MathML: {sample['mathml'][:100]}...")
        
        try:
            # 변환 실행
            result = converter.convert_mathml(999999 + i, sample['mathml'])
            
            print(f"✅ 변환 성공: {result.success}")
            print(f"📊 변환 타입: {result.conversion_type}")
            print(f"⏱️  처리 시간: {result.processing_time:.4f}초")
            
            if result.success:
                print(f"📄 변환 결과: {result.converted_content[:100]}...")
                
                # 예상 타입과 비교
                if result.conversion_type == sample['expected_type']:
                    print("✅ 타입 분류 정확")
                else:
                    print(f"⚠️  타입 분류 불일치 (예상: {sample['expected_type']}, 실제: {result.conversion_type})")
            else:
                print(f"❌ 변환 실패: {result.error_message}")
            
            results.append({
                'test_name': sample['name'],
                'success': result.success,
                'conversion_type': result.conversion_type,
                'expected_type': sample['expected_type'],
                'processing_time': result.processing_time,
                'error_message': result.error_message
            })
            
        except Exception as e:
            print(f"❌ 테스트 오류: {e}")
            results.append({
                'test_name': sample['name'],
                'success': False,
                'conversion_type': 'error',
                'expected_type': sample['expected_type'],
                'processing_time': 0,
                'error_message': str(e)
            })
    
    # 테스트 결과 요약
    print("\n" + "=" * 50)
    print("📊 테스트 결과 요약")
    print("=" * 50)
    
    total_tests = len(results)
    successful_tests = sum(1 for r in results if r['success'])
    type_correct = sum(1 for r in results if r['conversion_type'] == r['expected_type'])
    avg_processing_time = sum(r['processing_time'] for r in results) / total_tests
    
    print(f"📈 총 테스트: {total_tests}개")
    print(f"✅ 성공: {successful_tests}개 ({successful_tests/total_tests*100:.1f}%)")
    print(f"🎯 타입 정확: {type_correct}개 ({type_correct/total_tests*100:.1f}%)")
    print(f"⏱️  평균 처리 시간: {avg_processing_time:.4f}초")
    
    # 실패한 테스트 상세
    failed_tests = [r for r in results if not r['success']]
    if failed_tests:
        print(f"\n❌ 실패한 테스트:")
        for test in failed_tests:
            print(f"  - {test['test_name']}: {test['error_message']}")
    
    # 타입 분류 오류 상세
    type_errors = [r for r in results if r['conversion_type'] != r['expected_type'] and r['success']]
    if type_errors:
        print(f"\n⚠️  타입 분류 오류:")
        for test in type_errors:
            print(f"  - {test['test_name']}: 예상 {test['expected_type']} → 실제 {test['conversion_type']}")
    
    print("\n🎯 테스트 완료!")
    
    return results

if __name__ == "__main__":
    test_mathml_conversion()
