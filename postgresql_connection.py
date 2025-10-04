#!/usr/bin/env python3
"""
PostgreSQL 데이터베이스 연결 설정
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import os
from typing import List, Dict, Any, Optional
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PostgreSQLConnection:
    """PostgreSQL 데이터베이스 연결 클래스"""
    
    def __init__(self):
        self.connection = None
        self.cursor = None
        
    def connect(self):
        """데이터베이스 연결"""
        try:
            # 환경변수에서 데이터베이스 연결 정보 가져오기
            db_config = {
                'host': os.getenv('DB_HOST', 'localhost'),
                'port': os.getenv('DB_PORT', '5432'),
                'database': os.getenv('DB_NAME', 'dreamseed'),
                'user': os.getenv('DB_USER', 'postgres'),
                'password': os.getenv('DB_PASSWORD', 'password')
            }
            
            self.connection = psycopg2.connect(**db_config)
            self.cursor = self.connection.cursor(cursor_factory=RealDictCursor)
            logger.info("PostgreSQL 데이터베이스 연결 성공")
            return True
            
        except Exception as e:
            logger.error(f"PostgreSQL 연결 오류: {e}")
            return False
    
    def disconnect(self):
        """데이터베이스 연결 해제"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
        logger.info("PostgreSQL 데이터베이스 연결 해제")
    
    def execute_query(self, query: str, params: tuple = None) -> List[Dict[str, Any]]:
        """쿼리 실행"""
        try:
            if not self.connection or self.connection.closed:
                self.connect()
            
            self.cursor.execute(query, params)
            results = self.cursor.fetchall()
            return [dict(row) for row in results]
            
        except Exception as e:
            logger.error(f"쿼리 실행 오류: {e}")
            return []
    
    def get_math_questions(self, grade: str = None, subject: str = None, 
                          category_id: str = None, limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
        """수학 문제 조회"""
        try:
            # 기본 쿼리
            query = """
                SELECT 
                    q.question_id,
                    q.title,
                    q.content,
                    q.solution,
                    q.hints,
                    q.answer,
                    q.difficulty,
                    q.grade,
                    q.subject,
                    q.category_id,
                    c.category_name,
                    q.created_at,
                    q.updated_at
                FROM questions q
                LEFT JOIN categories c ON q.category_id = c.category_id
                WHERE 1=1
            """
            
            params = []
            param_count = 0
            
            # 필터 조건 추가
            if grade:
                param_count += 1
                query += f" AND q.grade = ${param_count}"
                params.append(grade)
            
            if subject:
                param_count += 1
                query += f" AND q.subject = ${param_count}"
                params.append(subject)
            
            if category_id:
                param_count += 1
                query += f" AND q.category_id = ${param_count}"
                params.append(category_id)
            
            # 정렬 및 페이징
            query += " ORDER BY q.created_at DESC"
            query += f" LIMIT ${param_count + 1} OFFSET ${param_count + 2}"
            params.extend([limit, offset])
            
            return self.execute_query(query, tuple(params))
            
        except Exception as e:
            logger.error(f"수학 문제 조회 오류: {e}")
            return []
    
    def get_question_by_id(self, question_id: str) -> Optional[Dict[str, Any]]:
        """ID로 단일 문제 조회"""
        try:
            query = """
                SELECT 
                    q.question_id,
                    q.title,
                    q.content,
                    q.solution,
                    q.hints,
                    q.answer,
                    q.difficulty,
                    q.grade,
                    q.subject,
                    q.category_id,
                    c.category_name,
                    q.created_at,
                    q.updated_at
                FROM questions q
                LEFT JOIN categories c ON q.category_id = c.category_id
                WHERE q.question_id = %s
            """
            
            results = self.execute_query(query, (question_id,))
            return results[0] if results else None
            
        except Exception as e:
            logger.error(f"문제 조회 오류: {e}")
            return None
    
    def get_categories(self, grade: str = None, subject: str = None) -> List[Dict[str, Any]]:
        """카테고리 조회"""
        try:
            query = """
                SELECT 
                    c.category_id,
                    c.category_name,
                    c.description,
                    c.grade,
                    c.subject,
                    COUNT(q.question_id) as question_count
                FROM categories c
                LEFT JOIN questions q ON c.category_id = q.category_id
                WHERE 1=1
            """
            
            params = []
            param_count = 0
            
            if grade:
                param_count += 1
                query += f" AND c.grade = ${param_count}"
                params.append(grade)
            
            if subject:
                param_count += 1
                query += f" AND c.subject = ${param_count}"
                params.append(subject)
            
            query += " GROUP BY c.category_id, c.category_name, c.description, c.grade, c.subject"
            query += " ORDER BY c.category_name"
            
            return self.execute_query(query, tuple(params))
            
        except Exception as e:
            logger.error(f"카테고리 조회 오류: {e}")
            return []

# 전역 데이터베이스 연결 인스턴스
db_connection = PostgreSQLConnection()
