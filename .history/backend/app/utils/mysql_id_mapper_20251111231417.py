"""
MySQL ID와 PostgreSQL UUID 간 매핑 유틸리티

Legacy MySQL 데이터베이스와의 호환성을 위해 mysql_id_int 컬럼을 사용합니다.
"""
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional
import uuid


def get_problem_by_mysql_id(db: Session, mysql_id: int) -> Optional[dict]:
    """
    MySQL ID로 문제 조회
    
    Args:
        db: 데이터베이스 세션
        mysql_id: MySQL의 원래 문제 ID
        
    Returns:
        문제 데이터 또는 None
    """
    result = db.execute(
        text("""
            SELECT id, title, description, difficulty, category, 
                   mysql_id_int, metadata, created_at
            FROM problems
            WHERE mysql_id_int = :mysql_id
            LIMIT 1
        """),
        {"mysql_id": mysql_id}
    ).fetchone()
    
    if not result:
        return None
    
    return {
        "id": str(result.id),
        "mysql_id": result.mysql_id_int,
        "title": result.title,
        "description": result.description,
        "difficulty": result.difficulty,
        "category": result.category,
        "metadata": result.metadata,
        "created_at": result.created_at.isoformat() if result.created_at else None
    }


def get_uuid_by_mysql_id(db: Session, mysql_id: int) -> Optional[uuid.UUID]:
    """
    MySQL ID로 PostgreSQL UUID 조회
    
    Args:
        db: 데이터베이스 세션
        mysql_id: MySQL의 원래 문제 ID
        
    Returns:
        PostgreSQL UUID 또는 None
    """
    result = db.execute(
        text("SELECT id FROM problems WHERE mysql_id_int = :mysql_id LIMIT 1"),
        {"mysql_id": mysql_id}
    ).fetchone()
    
    return result.id if result else None


def get_mysql_id_by_uuid(db: Session, problem_uuid: uuid.UUID) -> Optional[int]:
    """
    PostgreSQL UUID로 MySQL ID 조회
    
    Args:
        db: 데이터베이스 세션
        problem_uuid: PostgreSQL UUID
        
    Returns:
        MySQL ID 또는 None
    """
    result = db.execute(
        text("SELECT mysql_id_int FROM problems WHERE id = :uuid LIMIT 1"),
        {"uuid": str(problem_uuid)}
    ).fetchone()
    
    return result.mysql_id_int if result else None


def bulk_get_uuids_by_mysql_ids(db: Session, mysql_ids: list[int]) -> dict[int, uuid.UUID]:
    """
    여러 MySQL ID를 한 번에 UUID로 변환
    
    Args:
        db: 데이터베이스 세션
        mysql_ids: MySQL ID 리스트
        
    Returns:
        {mysql_id: uuid} 매핑 딕셔너리
    """
    if not mysql_ids:
        return {}
    
    results = db.execute(
        text("""
            SELECT mysql_id_int, id 
            FROM problems 
            WHERE mysql_id_int = ANY(:ids)
        """),
        {"ids": mysql_ids}
    ).fetchall()
    
    return {row.mysql_id_int: row.id for row in results}
