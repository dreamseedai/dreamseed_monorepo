#!/usr/bin/env python3
"""
ID 기반 MathML 변환 시스템
"""

import asyncio
import aiohttp
import json
import sqlite3
import os
from datetime import datetime
from batch_mathml_processor import BatchMathMLProcessor, ConversionResult

class IDBasedConverter:
    def __init__(self, api_key: str, db_path: str, batch_size: int = 50):
        self.api_key = api_key
        self.db_path = db_path
        self.batch_size = batch_size
        self.processor = BatchMathMLProcessor(api_key, batch_size)
        
    def load_mathml_ids(self, ids_file: str = "mathml_ids.json"):
        """저장된 MathML ID 목록 로드"""
        if not os.path.exists(ids_file):
            print(f"❌ ID 파일을 찾을 수 없습니다: {ids_file}")
            return []
        
        with open(ids_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"✅ {data['total_count']}개 MathML ID 로드 완료")
        return data['data']
    
    def get_mathml_by_ids(self, ids: list):
        """데이터베이스에서 특정 ID들의 MathML 데이터 조회"""
        if not ids:
            return []
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # ID 리스트를 문자열로 변환
        id_placeholders = ','.join('?' * len(ids))
        
        query = f"""
        SELECT id, question_id, mathml, subject, grade, title, content
        FROM questions 
        WHERE id IN ({id_placeholders})
        ORDER BY id
        """
        
        cursor.execute(query, ids)
        results = cursor.fetchall()
        
        # 딕셔너리로 변환
        data = []
        for row in results:
            data.append({
                'id': row[0],
                'question_id': row[1],
                'mathml': row[2],
                'subject': row[3],
                'grade': row[4],
                'title': row[5],
                'content': row[6]
            })
        
        conn.close()
        return data
    
    def save_conversion_results(self, results: list, batch_num: int):
        """변환 결과를 데이터베이스에 저장"""
        if not results:
            return
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # mathlive 컬럼이 있는지 확인하고 없으면 추가
        try:
            cursor.execute("ALTER TABLE questions ADD COLUMN mathlive TEXT")
            print("✅ mathlive 컬럼 추가됨")
        except sqlite3.OperationalError:
            pass  # 컬럼이 이미 존재
        
        # 변환 결과 업데이트
        success_count = 0
        for result in results:
            if result.success:
                cursor.execute("""
                    UPDATE questions 
                    SET mathlive = ? 
                    WHERE id = ?
                """, (result.converted_mathlive, result.question_id))
                success_count += 1
        
        conn.commit()
        conn.close()
        
        print(f"✅ 배치 {batch_num}: {success_count}/{len(results)}개 결과 저장 완료")
    
    async def convert_by_ids(self, mathml_ids: list, start_batch: int = 1):
        """ID 목록을 기반으로 변환 실행"""
        total_items = len(mathml_ids)
        total_batches = (total_items + self.batch_size - 1) // self.batch_size
        
        print(f"🚀 ID 기반 변환 시작: {total_items}개 항목, {total_batches}개 배치")
        print(f"📊 배치 크기: {self.batch_size}")
        
        processed_count = 0
        
        async with aiohttp.ClientSession() as session:
            for batch_num in range(start_batch - 1, total_batches):
                start_idx = batch_num * self.batch_size
                end_idx = min(start_idx + self.batch_size, total_items)
                batch_ids = mathml_ids[start_idx:end_idx]
                
                print(f"\n📦 배치 {batch_num + 1}/{total_batches} 처리 중... ({len(batch_ids)}개 ID)")
                
                # 해당 ID들의 MathML 데이터 조회
                batch_data = self.get_mathml_by_ids(batch_ids)
                
                if not batch_data:
                    print(f"⚠️ 배치 {batch_num + 1}: 데이터 없음")
                    continue
                
                # 변환 실행
                results = await self.processor.process_batch(batch_data)
                
                # 결과 저장
                self.save_conversion_results(results, batch_num + 1)
                
                processed_count += len(results)
                print(f"✅ 배치 {batch_num + 1} 완료. 총 처리: {processed_count}/{total_items}")
                
                # 배치 간 대기 (API 제한 고려)
                if batch_num < total_batches - 1:
                    await asyncio.sleep(2)
        
        print(f"\n🎯 ID 기반 변환 완료: {processed_count}개 항목 처리")

def main():
    """메인 실행 함수"""
    # 설정
    api_key = os.getenv('OPENAI_API_KEY', 'test-key')
    db_path = "mpcstudy_db.sql"
    batch_size = 50  # 최적 배치 크기
    
    if not os.path.exists(db_path):
        print(f"❌ 데이터베이스 파일을 찾을 수 없습니다: {db_path}")
        return
    
    # ID 기반 변환기 생성
    converter = IDBasedConverter(api_key, db_path, batch_size)
    
    # MathML ID 로드
    mathml_ids = converter.load_mathml_ids()
    
    if not mathml_ids:
        print("❌ 변환할 MathML ID가 없습니다.")
        return
    
    # ID만 추출 (데이터베이스 조회용)
    ids = [item['id'] for item in mathml_ids]
    
    # 변환 실행
    asyncio.run(converter.convert_by_ids(ids))

if __name__ == "__main__":
    main()
