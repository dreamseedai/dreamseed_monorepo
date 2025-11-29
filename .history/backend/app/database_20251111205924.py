"""
Database configuration and session management
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

# 환경 변수에서 DATABASE_URL 로드
from sqlalchemy.orm import sessionmaker, Session, DeclarativeBase

# PostgreSQL 연결 설정 (psycopg2 드라이버 사용)
# 비밀번호에 @ 기호가 있으면 URL 인코딩 필요 (%40)
DATABASE_URL = "postgresql+psycopg2://postgres:DreamSeedAi%400908@127.0.0.1:5432/dreamseed"

# SQLAlchemy 엔진 생성
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # 연결 유효성 검사
    pool_size=5,         # 연결 풀 크기
    max_overflow=10,     # 최대 추가 연결
)

# 세션 팩토리
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base 클래스 (모든 모델이 상속)
Base = declarative_base()


# Dependency for FastAPI
def get_db():
    """
    FastAPI dependency for database session
    
    Usage:
        @app.get("/items")
        def read_items(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Health check
def check_db_connection():
    """Check database connectivity"""
    try:
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        return True
    except Exception as e:
        print(f"Database connection failed: {e}")
        return False
