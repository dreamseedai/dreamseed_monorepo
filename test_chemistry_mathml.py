#!/usr/bin/env python3
"""
화학 MathML 변환 테스트 스크립트
"""

import asyncio
import aiohttp
from batch_mathml_processor import BatchMathMLProcessor

# 화학 MathML 예시 데이터
CHEMISTRY_MATHML_EXAMPLES = [
    {
        'question_id': 'C001',
        'mathml': '<math><mrow><mi>H</mi><mn>2</mn><mo>+</mo><mi>Cl</mi><mn>2</mn><mo>→</mo><mn>2</mn><mi>HCl</mi></mrow></math>',
        'subject': 'C',
        'grade': 'G11',
        'title': '수소와 염소의 반응',
        'content': '수소와 염소가 반응하여 염화수소가 생성되는 반응식'
    },
    {
        'question_id': 'C002',
        'mathml': '<math><mrow><mi>CH</mi><mn>4</mn><mo>+</mo><mn>2</mn><mi>O</mi><mn>2</mn><mo>→</mo><mi>CO</mi><mn>2</mn><mo>+</mo><mn>2</mn><mi>H</mi><mn>2</mn><mi>O</mi></mrow></math>',
        'subject': 'C',
        'grade': 'G11',
        'title': '메탄 연소 반응',
        'content': '메탄이 산소와 반응하여 이산화탄소와 물이 생성되는 연소 반응'
    },
    {
        'question_id': 'C003',
        'mathml': '<math><mrow><msup><mi>Na</mi><mo>+</mo></msup><mo>+</mo><msup><mi>Cl</mi><mo>-</mo></msup><mo>→</mo><mi>NaCl</mi></mrow></math>',
        'subject': 'C',
        'grade': 'G11',
        'title': '이온 결합',
        'content': '나트륨 이온과 염소 이온이 결합하여 염화나트륨이 생성되는 과정'
    },
    {
        'question_id': 'P001',
        'mathml': '<math><mrow><mi>F</mi><mo>=</mo><mi>m</mi><mi>a</mi></mrow></math>',
        'subject': 'P',
        'grade': 'G11',
        'title': '뉴턴의 제2법칙',
        'content': '힘은 질량과 가속도의 곱과 같다'
    },
    {
        'question_id': 'B001',
        'mathml': '<math><mrow><mi>C</mi><mn>6</mn><mi>H</mi><mn>12</mn><mi>O</mi><mn>6</mn><mo>+</mo><mn>6</mn><mi>O</mi><mn>2</mn><mo>→</mo><mn>6</mn><mi>CO</mi><mn>2</mn><mo>+</mo><mn>6</mn><mi>H</mi><mn>2</mn><mi>O</mi><mo>+</mo><mi>ATP</mi></mrow></math>',
        'subject': 'B',
        'grade': 'G11',
        'title': '세포 호흡',
        'content': '포도당이 산소와 반응하여 에너지를 생성하는 과정'
    }
]

async def test_chemistry_conversion():
    """화학 MathML 변환 테스트"""
    print("🧪 화학 MathML 변환 테스트 시작")
    print("=" * 50)
    
    # API 키 확인
    api_key = 'test-key'  # 테스트 모드
    
    # 프로세서 생성
    processor = BatchMathMLProcessor(api_key, batch_size=5)
    
    # 테스트 데이터로 변환
    async with aiohttp.ClientSession() as session:
        for item in CHEMISTRY_MATHML_EXAMPLES:
            print(f"\n📝 {item['subject']} - {item['title']}")
            print(f"MathML: {item['mathml']}")
            
            try:
                result = await processor.convert_single_mathml(
                    session, 
                    item['question_id'], 
                    item['mathml'], 
                    item['subject']
                )
                
                print(f"✅ 변환 성공: {result.converted_mathlive}")
                print(f"⏱️ 처리 시간: {result.processing_time:.2f}초")
                
            except Exception as e:
                print(f"❌ 변환 실패: {e}")
    
    print("\n🎯 화학 MathML 변환 테스트 완료!")

if __name__ == "__main__":
    asyncio.run(test_chemistry_conversion())
