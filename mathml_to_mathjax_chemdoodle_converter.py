#!/usr/bin/env python3
"""
MathML to MathJax + ChemDoodle Converter
DreamSeed AI 프로젝트용 MathML 변환기
"""

import os
import re
import json
import asyncio
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('mathml_conversion.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class ConversionResult:
    question_id: int
    original_mathml: str
    converted_content: str
    conversion_type: str  # 'mathjax', 'chemdoodle', 'hybrid'
    success: bool
    error_message: Optional[str] = None
    processing_time: float = 0.0

class MathMLConverter:
    """MathML을 MathJax + ChemDoodle로 변환하는 메인 클래스"""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.conn = None
        self.conversion_stats = {
            'total_processed': 0,
            'mathjax_conversions': 0,
            'chemdoodle_conversions': 0,
            'hybrid_conversions': 0,
            'errors': 0,
            'start_time': None,
            'end_time': None
        }
        
    def connect_database(self):
        """데이터베이스 연결"""
        try:
            self.conn = psycopg2.connect(self.database_url)
            logger.info("✅ 데이터베이스 연결 성공")
        except Exception as e:
            logger.error(f"❌ 데이터베이스 연결 실패: {e}")
            raise
    
    def disconnect_database(self):
        """데이터베이스 연결 해제"""
        if self.conn:
            self.conn.close()
            logger.info("✅ 데이터베이스 연결 해제")
    
    def classify_mathml_type(self, mathml_content: str) -> str:
        """MathML 내용을 분석하여 변환 타입 결정"""
        
        # 화학 관련 패턴 감지
        chemistry_patterns = [
            r'class=[\'"]wrs_chemistry[\'"]',
            r'<mi>[A-Z][a-z]?\d*</mi>',  # 원소 기호
            r'<msub>.*?</msub>',         # 아래첨자
            r'<msup>.*?</msup>',         # 위첨자
            r'<mo>→</mo>',               # 반응 화살표
            r'<mo>⇌</mo>',               # 평형 화살표
            r'<mo>+</mo>',               # 화학 결합
            r'<mo>-</mo>',               # 화학 결합
            r'<mo>=</mo>',               # 화학 결합
            r'<mo>≡</mo>',               # 삼중 결합
            r'<mtext>mol</mtext>',       # 화학 단위
            r'<mtext>atm</mtext>',       # 화학 단위
            r'<mtext>°C</mtext>',        # 온도
            r'<mtext>K</mtext>',         # 온도
            r'<mtext>M</mtext>',         # 농도
            r'<mtext>J</mtext>',         # 에너지
            r'<mtext>cal</mtext>',       # 에너지
        ]
        
        # 복잡한 화학 구조 패턴
        complex_chemistry_patterns = [
            r'<mtext>벤젠</mtext>',
            r'<mtext>나프탈렌</mtext>',
            r'<mtext>스테로이드</mtext>',
            r'<mtext>고리</mtext>',
            r'<mtext>구조</mtext>',
            r'<mtext>분자</mtext>',
            r'<mtext>이성질체</mtext>',
            r'<mtext>입체</mtext>',
        ]
        
        # 고급 수학 패턴
        advanced_math_patterns = [
            r'<mfrac>.*?</mfrac>',       # 분수
            r'<msqrt>.*?</msqrt>',       # 제곱근
            r'<msup>.*?</msup>',         # 위첨자
            r'<msub>.*?</msub>',         # 아래첨자
            r'<msubsup>.*?</msubsup>',   # 위아래첨자
            r'<munder>.*?</munder>',     # 아래선
            r'<mover>.*?</mover>',       # 위선
            r'<munderover>.*?</munderover>', # 위아래선
            r'<mtable>.*?</mtable>',     # 행렬
            r'<mtr>.*?</mtr>',           # 행
            r'<mtd>.*?</mtd>',           # 셀
            r'<mroot>.*?</mroot>',       # n제곱근
            r'<mtext>∫</mtext>',         # 적분
            r'<mtext>∑</mtext>',         # 합
            r'<mtext>∏</mtext>',         # 곱
            r'<mtext>lim</mtext>',       # 극한
            r'<mtext>∂</mtext>',         # 편미분
            r'<mtext>∇</mtext>',         # 그라디언트
            r'<mtext>∮</mtext>',         # 선적분
        ]
        
        # 복잡한 화학 구조 감지
        if any(re.search(pattern, mathml_content, re.IGNORECASE) for pattern in complex_chemistry_patterns):
            return 'chemdoodle'
        
        # 기본 화학 패턴 감지
        chemistry_count = sum(1 for pattern in chemistry_patterns if re.search(pattern, mathml_content, re.IGNORECASE))
        if chemistry_count >= 3:  # 3개 이상의 화학 패턴이 있으면 화학으로 분류
            return 'chemdoodle'
        
        # 고급 수학 패턴 감지
        math_count = sum(1 for pattern in advanced_math_patterns if re.search(pattern, mathml_content, re.IGNORECASE))
        if math_count >= 2:  # 2개 이상의 고급 수학 패턴이 있으면 고급 수학으로 분류
            return 'mathjax'
        
        # 기본 수학으로 분류
        return 'mathjax'
    
    def convert_mathml_to_mathjax(self, mathml_content: str) -> str:
        """MathML을 MathJax LaTeX로 변환"""
        try:
            # MathML을 LaTeX로 변환하는 로직
            # 실제 구현에서는 더 정교한 변환 로직이 필요
            
            # 기본 변환 규칙
            latex_content = mathml_content
            
            # MathML 태그를 LaTeX로 변환
            latex_content = re.sub(r'<math[^>]*>', '', latex_content)
            latex_content = re.sub(r'</math>', '', latex_content)
            latex_content = re.sub(r'<mi>([^<]+)</mi>', r'\\text{\1}', latex_content)
            latex_content = re.sub(r'<mn>([^<]+)</mn>', r'\1', latex_content)
            latex_content = re.sub(r'<mo>([^<]+)</mo>', r'\1', latex_content)
            latex_content = re.sub(r'<mfrac>([^<]+)</mfrac>', r'\\frac{\1}', latex_content)
            latex_content = re.sub(r'<msup>([^<]+)</msup>', r'^{\1}', latex_content)
            latex_content = re.sub(r'<msub>([^<]+)</msub>', r'_{\1}', latex_content)
            latex_content = re.sub(r'<msqrt>([^<]+)</msqrt>', r'\\sqrt{\1}', latex_content)
            
            # 공백 정리
            latex_content = re.sub(r'\s+', ' ', latex_content).strip()
            
            return f"\\[{latex_content}\\]"
            
        except Exception as e:
            logger.error(f"MathJax 변환 오류: {e}")
            return mathml_content
    
    def convert_mathml_to_chemdoodle(self, mathml_content: str) -> str:
        """MathML을 ChemDoodle 구조로 변환"""
        try:
            # MathML을 ChemDoodle 구조로 변환하는 로직
            # 실제 구현에서는 더 정교한 변환 로직이 필요
            
            # 화학 구조식 감지 및 변환
            if '벤젠' in mathml_content or 'benzene' in mathml_content.lower():
                return json.dumps({
                    "type": "benzene",
                    "data": "",
                    "description": "벤젠 고리"
                })
            elif '나프탈렌' in mathml_content or 'naphthalene' in mathml_content.lower():
                return json.dumps({
                    "type": "naphthalene", 
                    "data": "",
                    "description": "나프탈렌"
                })
            elif '스테로이드' in mathml_content or 'steroid' in mathml_content.lower():
                return json.dumps({
                    "type": "steroid",
                    "data": "",
                    "description": "스테로이드"
                })
            else:
                # 기본 화학 반응식으로 변환
                return json.dumps({
                    "type": "reaction",
                    "data": mathml_content,
                    "description": "화학 반응식"
                })
                
        except Exception as e:
            logger.error(f"ChemDoodle 변환 오류: {e}")
            return json.dumps({
                "type": "error",
                "data": mathml_content,
                "description": f"변환 오류: {str(e)}"
            })
    
    def convert_mathml(self, question_id: int, mathml_content: str) -> ConversionResult:
        """MathML을 변환하고 결과 반환"""
        start_time = datetime.now()
        
        try:
            # MathML 타입 분류
            conversion_type = self.classify_mathml_type(mathml_content)
            
            # 변환 실행
            if conversion_type == 'mathjax':
                converted_content = self.convert_mathml_to_mathjax(mathml_content)
            elif conversion_type == 'chemdoodle':
                converted_content = self.convert_mathml_to_chemdoodle(mathml_content)
            else:
                # 하이브리드 변환 (수학 + 화학)
                mathjax_part = self.convert_mathml_to_mathjax(mathml_content)
                chemdoodle_part = self.convert_mathml_to_chemdoodle(mathml_content)
                converted_content = json.dumps({
                    "mathjax": mathjax_part,
                    "chemdoodle": chemdoodle_part,
                    "type": "hybrid"
                })
                conversion_type = 'hybrid'
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            result = ConversionResult(
                question_id=question_id,
                original_mathml=mathml_content,
                converted_content=converted_content,
                conversion_type=conversion_type,
                success=True,
                processing_time=processing_time
            )
            
            # 통계 업데이트
            self.conversion_stats['total_processed'] += 1
            if conversion_type == 'mathjax':
                self.conversion_stats['mathjax_conversions'] += 1
            elif conversion_type == 'chemdoodle':
                self.conversion_stats['chemdoodle_conversions'] += 1
            elif conversion_type == 'hybrid':
                self.conversion_stats['hybrid_conversions'] += 1
            
            return result
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            error_message = str(e)
            
            result = ConversionResult(
                question_id=question_id,
                original_mathml=mathml_content,
                converted_content=mathml_content,  # 원본 유지
                conversion_type='error',
                success=False,
                error_message=error_message,
                processing_time=processing_time
            )
            
            self.conversion_stats['errors'] += 1
            logger.error(f"변환 오류 (Question ID: {question_id}): {error_message}")
            
            return result
    
    def get_mathml_questions(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """데이터베이스에서 MathML이 포함된 문제 조회"""
        try:
            cursor = self.conn.cursor(cursor_factory=RealDictCursor)
            
            query = """
                SELECT que_id, que_en_solution, que_en_answers, que_en_hint
                FROM tbl_question 
                WHERE (que_en_solution LIKE '%<math%' OR 
                       que_en_answers LIKE '%<math%' OR 
                       que_en_hint LIKE '%<math%')
                AND que_status = 1
                ORDER BY que_id
                LIMIT %s OFFSET %s
            """
            
            cursor.execute(query, (limit, offset))
            results = cursor.fetchall()
            cursor.close()
            
            logger.info(f"✅ {len(results)}개 문제 조회 완료 (offset: {offset})")
            return results
            
        except Exception as e:
            logger.error(f"❌ 문제 조회 실패: {e}")
            return []
    
    def save_conversion_result(self, result: ConversionResult, output_file: str):
        """변환 결과를 파일에 저장"""
        try:
            result_data = {
                'question_id': result.question_id,
                'original_mathml': result.original_mathml,
                'converted_content': result.converted_content,
                'conversion_type': result.conversion_type,
                'success': result.success,
                'error_message': result.error_message,
                'processing_time': result.processing_time,
                'timestamp': datetime.now().isoformat()
            }
            
            # JSON Lines 형식으로 저장
            with open(output_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(result_data, ensure_ascii=False) + '\n')
                
        except Exception as e:
            logger.error(f"❌ 결과 저장 실패: {e}")
    
    def process_batch(self, batch_size: int = 100, total_limit: int = 0, output_file: str = "conversion_results.jsonl"):
        """배치 처리로 MathML 변환 실행"""
        self.conversion_stats['start_time'] = datetime.now()
        
        try:
            self.connect_database()
            
            offset = 0
            processed_count = 0
            
            while True:
                # 배치 조회
                questions = self.get_mathml_questions(batch_size, offset)
                
                if not questions:
                    break
                
                # 배치 처리
                for question in questions:
                    question_id = question['que_id']
                    
                    # MathML 추출 및 변환
                    mathml_contents = []
                    
                    # solution에서 MathML 추출
                    if question['que_en_solution'] and '<math' in question['que_en_solution']:
                        mathml_contents.append(('solution', question['que_en_solution']))
                    
                    # answers에서 MathML 추출
                    if question['que_en_answers'] and '<math' in question['que_en_answers']:
                        mathml_contents.append(('answers', question['que_en_answers']))
                    
                    # hint에서 MathML 추출
                    if question['que_en_hint'] and '<math' in question['que_en_hint']:
                        mathml_contents.append(('hint', question['que_en_hint']))
                    
                    # 각 MathML 변환
                    for field_type, content in mathml_contents:
                        # MathML 태그 추출
                        mathml_matches = re.findall(r'<math[^>]*>.*?</math>', content, re.DOTALL)
                        
                        for mathml in mathml_matches:
                            result = self.convert_mathml(question_id, mathml)
                            self.save_conversion_result(result, output_file)
                            
                            processed_count += 1
                            
                            if processed_count % 100 == 0:
                                logger.info(f"진행 상황: {processed_count}개 처리 완료")
                
                offset += batch_size
                
                # 총 제한 확인
                if total_limit > 0 and processed_count >= total_limit:
                    break
            
            self.conversion_stats['end_time'] = datetime.now()
            self.print_conversion_summary()
            
        except Exception as e:
            logger.error(f"❌ 배치 처리 실패: {e}")
        finally:
            self.disconnect_database()
    
    def print_conversion_summary(self):
        """변환 결과 요약 출력"""
        duration = self.conversion_stats['end_time'] - self.conversion_stats['start_time']
        
        print("\n" + "="*60)
        print("🎯 MathML 변환 완료 요약")
        print("="*60)
        print(f"📊 총 처리된 문제: {self.conversion_stats['total_processed']:,}개")
        print(f"📐 MathJax 변환: {self.conversion_stats['mathjax_conversions']:,}개")
        print(f"🧪 ChemDoodle 변환: {self.conversion_stats['chemdoodle_conversions']:,}개")
        print(f"🔄 하이브리드 변환: {self.conversion_stats['hybrid_conversions']:,}개")
        print(f"❌ 오류: {self.conversion_stats['errors']:,}개")
        print(f"⏱️  총 소요 시간: {duration}")
        print(f"⚡ 평균 처리 속도: {self.conversion_stats['total_processed'] / duration.total_seconds():.2f}개/초")
        print("="*60)

def main():
    """메인 실행 함수"""
    # 환경 변수에서 데이터베이스 URL 가져오기
    database_url = os.getenv('DATABASE_URL', 'postgresql://postgres:password@localhost:5432/dreamseed')
    
    # 변환기 초기화
    converter = MathMLConverter(database_url)
    
    # 배치 처리 실행
    converter.process_batch(
        batch_size=100,
        total_limit=1000,  # 테스트용으로 1000개만 처리
        output_file="mathml_conversion_results.jsonl"
    )

if __name__ == "__main__":
    main()
