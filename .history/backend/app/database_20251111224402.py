"""
Database configuration and session management
"""
from sqlalchemy import create_engine, URL
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

# PostgreSQL 연결 설정 (URL 객체 사용)
DATABASE_URL = URL.create(
    drivername="postgresql+psycopg2",
    username="postgres",
    password="DreamSeedAi0908",
    host="127.0.0.1",
    port=5432,
    database="dreamseed"
)

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
