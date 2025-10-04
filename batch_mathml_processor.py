#!/usr/bin/env python3
"""
GPT-4.1 mini batch MathML 변환 시스템
100 단위로 배치 처리하여 효율적으로 전체 데이터 변환
"""

import os
import json
import time
import asyncio
import aiohttp
from typing import List, Dict, Any
from dataclasses import dataclass
from pathlib import Path
import logging

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('batch_conversion.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class ConversionResult:
    question_id: str
    original_mathml: str
    converted_mathlive: str
    success: bool
    error_message: str = ""
    processing_time: float = 0.0

class BatchMathMLProcessor:
    def __init__(self, api_key: str, batch_size: int = 100):
        self.api_key = api_key
        self.batch_size = batch_size
        self.base_url = "https://api.openai.com/v1/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
    async def convert_single_mathml(self, session: aiohttp.ClientSession, 
                                  question_id: str, mathml: str, subject: str = 'M') -> ConversionResult:
        """단일 MathML을 MathLive 형식으로 변환 (수학/화학/물리/생물 지원)"""
        start_time = time.time()
        
        # 과목별 시스템 프롬프트 설정
        subject_prompts = {
            'M': "당신은 MathML을 LaTeX로 변환하는 수학 전문가입니다. 수학 공식의 의미를 정확히 보존하면서 변환해주세요.",
            'C': "당신은 MathML을 LaTeX로 변환하는 화학 전문가입니다. 화학 반응식, 분자식, 이온식을 정확히 변환해주세요.",
            'P': "당신은 MathML을 LaTeX로 변환하는 물리 전문가입니다. 물리 공식과 과학적 표기법을 정확히 변환해주세요.",
            'B': "당신은 MathML을 LaTeX로 변환하는 생물 전문가입니다. 생물학적 공식과 과학적 표기법을 정확히 변환해주세요."
        }
        
        system_prompt = subject_prompts.get(subject, subject_prompts['M'])
        
        prompt = f"""
다음 {subject} MathML을 MathLive 형식으로 변환해주세요. {subject} 공식의 의미를 정확히 보존하면서 LaTeX 형식으로 출력해주세요.

MathML:
{mathml}

변환된 LaTeX (MathLive 형식):
"""
        
        payload = {
            "model": "gpt-4.1-mini",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 1000,
            "temperature": 0.1
        }
        
        # 테스트 모드 처리
        if not self.api_key or self.api_key == 'test-key':
            await asyncio.sleep(0.1)  # API 호출 시뮬레이션
            mock_result = f"\\text{{Mock {subject} MathLive: }} {mathml[:50]}..."
            return ConversionResult(
                question_id=question_id,
                original_mathml=mathml,
                converted_mathlive=mock_result,
                success=True,
                error_message=None,
                processing_time=time.time() - start_time
            )
        
        try:
            async with session.post(self.base_url, headers=self.headers, json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    converted = result['choices'][0]['message']['content'].strip()
                    processing_time = time.time() - start_time
                    
                    return ConversionResult(
                        question_id=question_id,
                        original_mathml=mathml,
                        converted_mathlive=converted,
                        success=True,
                        processing_time=processing_time
                    )
                else:
                    error_text = await response.text()
                    logger.error(f"API 오류 {response.status}: {error_text}")
                    return ConversionResult(
                        question_id=question_id,
                        original_mathml=mathml,
                        converted_mathlive="",
                        success=False,
                        error_message=f"API 오류 {response.status}",
                        processing_time=time.time() - start_time
                    )
        except Exception as e:
            logger.error(f"변환 실패 {question_id}: {str(e)}")
            return ConversionResult(
                question_id=question_id,
                original_mathml=mathml,
                converted_mathlive="",
                success=False,
                error_message=str(e),
                processing_time=time.time() - start_time
            )
    
    async def process_batch(self, batch_data: List[Dict[str, Any]]) -> List[ConversionResult]:
        """배치 단위로 MathML 변환 처리"""
        logger.info(f"배치 처리 시작: {len(batch_data)}개 항목")
        
        async with aiohttp.ClientSession() as session:
            tasks = []
            for item in batch_data:
                question_id = item.get('question_id', '')
                mathml = item.get('mathml', '')
                if mathml.strip():
                    task = self.convert_single_mathml(session, question_id, mathml, item.get('subject', 'M'))
                    tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 예외 처리
            processed_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    processed_results.append(ConversionResult(
                        question_id=batch_data[i].get('question_id', ''),
                        original_mathml=batch_data[i].get('mathml', ''),
                        converted_mathlive="",
                        success=False,
                        error_message=str(result)
                    ))
                else:
                    processed_results.append(result)
            
            return processed_results
    
    def load_data_from_database(self, limit: int = None, offset: int = 0) -> List[Dict[str, Any]]:
        """데이터베이스에서 MathML 데이터 로드 (페이징 지원)"""
        logger.info(f"데이터베이스에서 {limit or '모든'} MathML 데이터 로드 (offset: {offset})")
        
        try:
            # PostgreSQL 연결 시도
            import psycopg2
            from psycopg2.extras import RealDictCursor
            
            # 데이터베이스 연결 (환경변수에서 설정)
            database_url = os.getenv('DATABASE_URL', 'postgresql://user:password@localhost/dreamseed')
            conn = psycopg2.connect(database_url)
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # MathML이 있는 문제만 조회 (페이징 지원)
            query = """
                SELECT question_id, mathml, subject, grade, title, content
                FROM questions 
                WHERE mathml IS NOT NULL 
                AND mathml != '' 
                AND mathml != '<math></math>'
                AND LENGTH(mathml) > 10
                ORDER BY question_id
            """
            
            if limit:
                query += f" LIMIT {limit} OFFSET {offset}"
            
            cursor.execute(query)
            data = cursor.fetchall()
            
            # 딕셔너리로 변환
            result = []
            for row in data:
                result.append({
                    'question_id': row['question_id'],
                    'mathml': row['mathml'],
                    'subject': row['subject'],
                    'grade': row['grade'],
                    'title': row['title'],
                    'content': row['content']
                })
            
            cursor.close()
            conn.close()
            
            logger.info(f"데이터베이스에서 {len(result)}개 MathML 항목 로드 완료")
            return result
            
        except ImportError:
            logger.warning("psycopg2가 설치되지 않음. 예시 데이터 사용")
        except Exception as e:
            logger.warning(f"데이터베이스 연결 실패: {e}. 예시 데이터 사용")
        
        # 폴백: 예시 데이터 (실제로는 DB에서 로드)
        sample_data = []
        start_idx = offset + 1
        end_idx = start_idx + (limit or 100)
        
        for i in range(start_idx, end_idx):
            sample_data.append({
                'question_id': f'Q{i:06d}',
                'mathml': f'<math><mi>x</mi><mo>+</mo><mi>y</mi><mo>=</mo><mn>5</mn></math>',
                'subject': 'M',
                'grade': 'G11',
                'title': f'수학 문제 {i}',
                'content': f'문제 내용 {i}'
            })
        
        return sample_data
    
    def save_results(self, results: List[ConversionResult], batch_num: int):
        """변환 결과를 파일로 저장"""
        output_file = f"conversion_results_batch_{batch_num:03d}.json"
        
        # 결과를 JSON으로 저장
        json_results = []
        for result in results:
            json_results.append({
                'question_id': result.question_id,
                'original_mathml': result.original_mathml,
                'converted_mathlive': result.converted_mathlive,
                'success': result.success,
                'error_message': result.error_message,
                'processing_time': result.processing_time
            })
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(json_results, f, ensure_ascii=False, indent=2)
        
        logger.info(f"배치 {batch_num} 결과 저장: {output_file}")
        
        # 통계 출력
        success_count = sum(1 for r in results if r.success)
        total_time = sum(r.processing_time for r in results)
        
        logger.info(f"배치 {batch_num} 완료: {success_count}/{len(results)} 성공, "
                   f"평균 처리시간: {total_time/len(results):.2f}초")
    
    async def run_full_conversion(self, total_limit: int = None):
        """전체 변환 프로세스 실행"""
        logger.info("=== GPT-4.1 mini batch MathML 변환 시작 ===")
        
        # 데이터 로드
        all_data = self.load_data_from_database(total_limit)
        total_items = len(all_data)
        total_batches = (total_items + self.batch_size - 1) // self.batch_size
        
        logger.info(f"총 {total_items}개 항목을 {total_batches}개 배치로 처리")
        
        # 배치별 처리
        for batch_num in range(total_batches):
            start_idx = batch_num * self.batch_size
            end_idx = min(start_idx + self.batch_size, total_items)
            batch_data = all_data[start_idx:end_idx]
            
            logger.info(f"배치 {batch_num + 1}/{total_batches} 처리 중... "
                       f"({start_idx + 1}-{end_idx})")
            
            # 배치 처리
            results = await self.process_batch(batch_data)
            
            # 결과 저장
            self.save_results(results, batch_num + 1)
            
            # 배치 간 대기 (API 제한 고려)
            if batch_num < total_batches - 1:
                wait_time = 2  # 2초 대기
                logger.info(f"다음 배치까지 {wait_time}초 대기...")
                await asyncio.sleep(wait_time)
        
        logger.info("=== 전체 변환 완료 ===")

def main():
    """메인 실행 함수"""
    # OpenAI API 키 로드
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        logger.error("OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")
        return
    
    # 배치 크기 설정 (100 단위)
    batch_size = 100
    
    # 프로세서 생성 및 실행
    processor = BatchMathMLProcessor(api_key, batch_size)
    
    # 전체 변환 실행 (예: 1000개 항목)
    asyncio.run(processor.run_full_conversion(total_limit=1000))

if __name__ == "__main__":
    main()