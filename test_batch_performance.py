#!/usr/bin/env python3
"""
배치 크기별 성능 테스트 스크립트
"""

import asyncio
import aiohttp
import time
import json
from batch_mathml_processor import BatchMathMLProcessor

# 테스트용 MathML 데이터 생성
def generate_test_data(count=100):
    """테스트용 MathML 데이터 생성"""
    test_data = []
    for i in range(count):
        test_data.append({
            'question_id': f'TEST_{i+1:03d}',
            'mathml': f'<math><mrow><mi>x</mi><mo>+</mo><mi>y</mi><mo>=</mo><mn>{i+1}</mn></mrow></math>',
            'subject': 'M',
            'grade': 'G11',
            'title': f'테스트 문제 {i+1}',
            'content': f'테스트 내용 {i+1}'
        })
    return test_data

async def test_batch_performance(batch_size, test_data, api_key='test-key'):
    """특정 배치 크기로 성능 테스트"""
    print(f"\n🧪 배치 크기 {batch_size} 테스트 시작...")
    
    processor = BatchMathMLProcessor(api_key, batch_size)
    
    start_time = time.time()
    
    try:
        async with aiohttp.ClientSession() as session:
            # 배치 처리
            results = await processor.process_batch(test_data)
            
        end_time = time.time()
        total_time = end_time - start_time
        
        # 결과 분석
        success_count = sum(1 for r in results if r.success)
        total_count = len(results)
        success_rate = (success_count / total_count * 100) if total_count > 0 else 0
        avg_time_per_item = total_time / total_count if total_count > 0 else 0
        items_per_second = total_count / total_time if total_time > 0 else 0
        
        return {
            'batch_size': batch_size,
            'total_items': total_count,
            'success_count': success_count,
            'success_rate': success_rate,
            'total_time': total_time,
            'avg_time_per_item': avg_time_per_item,
            'items_per_second': items_per_second
        }
        
    except Exception as e:
        print(f"❌ 배치 크기 {batch_size} 테스트 실패: {e}")
        return {
            'batch_size': batch_size,
            'error': str(e)
        }

async def run_performance_tests():
    """배치 크기별 성능 테스트 실행"""
    print("🚀 배치 크기 성능 테스트 시작")
    print("=" * 60)
    
    # 테스트 데이터 생성 (100개)
    test_data = generate_test_data(100)
    print(f"📊 테스트 데이터: {len(test_data)}개 항목")
    
    # 테스트할 배치 크기들
    batch_sizes = [5, 10, 20, 30, 50, 100]
    
    results = []
    
    for batch_size in batch_sizes:
        # 해당 배치 크기로 데이터 분할
        batch_data = test_data[:batch_size]  # 첫 N개만 사용
        
        result = await test_batch_performance(batch_size, batch_data)
        results.append(result)
        
        if 'error' not in result:
            print(f"✅ 배치 크기 {batch_size}: {result['success_rate']:.1f}% 성공, "
                  f"{result['items_per_second']:.2f} 항목/초")
        else:
            print(f"❌ 배치 크기 {batch_size}: 실패")
    
    # 결과 분석 및 추천
    print(f"\n📊 성능 테스트 결과:")
    print(f"{'배치크기':<8} {'성공률':<8} {'항목/초':<10} {'평균시간':<10} {'총시간':<8}")
    print("-" * 60)
    
    valid_results = [r for r in results if 'error' not in r]
    
    for result in valid_results:
        print(f"{result['batch_size']:<8} {result['success_rate']:<8.1f}% "
              f"{result['items_per_second']:<10.2f} {result['avg_time_per_item']:<10.3f}s "
              f"{result['total_time']:<8.2f}s")
    
    # 최적 배치 크기 추천
    if valid_results:
        # 성공률과 처리 속도의 균형을 고려
        best_result = max(valid_results, key=lambda x: x['success_rate'] * x['items_per_second'])
        
        print(f"\n💡 최적 배치 크기 추천: {best_result['batch_size']}")
        print(f"   - 성공률: {best_result['success_rate']:.1f}%")
        print(f"   - 처리 속도: {best_result['items_per_second']:.2f} 항목/초")
        print(f"   - 평균 처리 시간: {best_result['avg_time_per_item']:.3f}초/항목")
    
    # 결과 저장
    with open('batch_performance_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n📁 상세 결과 저장: batch_performance_results.json")

def analyze_real_world_scenarios():
    """실제 운영 시나리오 분석"""
    print(f"\n🌍 실제 운영 시나리오 분석:")
    print(f"{'시나리오':<20} {'총항목':<8} {'배치크기':<8} {'예상시간':<10} {'API호출':<8}")
    print("-" * 70)
    
    scenarios = [
        ("소규모 테스트", 100, 10, "2-5분", "10회"),
        ("중간 규모", 1000, 50, "20-40분", "20회"),
        ("대규모", 5000, 100, "1-2시간", "50회"),
        ("전체 변환", 10000, 100, "2-4시간", "100회")
    ]
    
    for scenario, total_items, batch_size, estimated_time, api_calls in scenarios:
        print(f"{scenario:<20} {total_items:<8} {batch_size:<8} {estimated_time:<10} {api_calls:<8}")
    
    print(f"\n💡 권장사항:")
    print(f"1. 개발/테스트: 10-20개 배치")
    print(f"2. 중간 규모: 30-50개 배치")
    print(f"3. 대규모: 50-100개 배치")
    print(f"4. API 제한 고려: 분당 60회 제한")

if __name__ == "__main__":
    asyncio.run(run_performance_tests())
    analyze_real_world_scenarios()
