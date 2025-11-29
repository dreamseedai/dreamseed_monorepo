"""
pytest 설정 파일
테스트용 데이터베이스, 클라이언트, 픽스처 정의
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine.url import URL

from app.main import app
from app.database import Base, get_db
from app.models.user import User
from app.models.problem import Problem
from app.core.security import get_password_hash
import uuid


# 테스트용 PostgreSQL 데이터베이스 (별도 DB 사용)
TEST_DATABASE_URL = URL.create(
    drivername="postgresql+psycopg2",
    username="postgres",
    password="DreamSeedAi@0908",
    host="127.0.0.1",
    port=5432,
    database="dreamseed_test"
)

engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db():
    """테스트용 데이터베이스 세션"""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db):
    """테스트용 FastAPI 클라이언트"""
    def override_get_db():
        try:
            yield db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def test_student(db):
    """테스트용 학생 계정"""
    user = User(
        id=uuid.uuid4(),
        email="student@test.com",
        hashed_password=get_password_hash("password123"),
        full_name="Test Student",
        role="student",
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_teacher(db):
    """테스트용 교사 계정"""
    user = User(
        id=uuid.uuid4(),
        email="teacher@test.com",
        hashed_password=get_password_hash("password123"),
        full_name="Test Teacher",
        role="teacher",
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_admin(db):
    """테스트용 관리자 계정"""
    user = User(
        id=uuid.uuid4(),
        email="admin@test.com",
        hashed_password=get_password_hash("password123"),
        full_name="Test Admin",
        role="admin",
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def student_token(client, test_student):
    """학생 JWT 토큰"""
    response = client.post(
        "/auth/login",
        json={
            "email": "student@test.com",
            "password": "password123"
        }
    )
    return response.json()["access_token"]


@pytest.fixture
def teacher_token(client, test_teacher):
    """교사 JWT 토큰"""
    response = client.post(
        "/auth/login",
        json={
            "email": "teacher@test.com",
            "password": "password123"
        }
    )
    return response.json()["access_token"]


@pytest.fixture
def admin_token(client, test_admin):
    """관리자 JWT 토큰"""
    response = client.post(
        "/auth/login",
        json={
            "email": "admin@test.com",
            "password": "password123"
        }
    )
    return response.json()["access_token"]


@pytest.fixture
def test_problem(db, test_teacher):
    """테스트용 문제"""
    problem = Problem(
        id=uuid.uuid4(),
        title="테스트 문제",
        description="이차방정식 x² - 5x + 6 = 0을 푸시오",
        difficulty="easy",
        category="수학",
        created_by=test_teacher.id
    )
    db.add(problem)
    db.commit()
    db.refresh(problem)
    return problem


@pytest.fixture
def auth_headers(student_token):
    """인증 헤더"""
    return {"Authorization": f"Bearer {student_token}"}


@pytest.fixture
def teacher_auth_headers(teacher_token):
    """교사 인증 헤더"""
    return {"Authorization": f"Bearer {teacher_token}"}
