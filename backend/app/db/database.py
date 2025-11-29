from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# 예: PostgreSQL
SQLALCHEMY_DATABASE_URL = "postgresql+psycopg2://postgres:0908@localhost:5432/postgres"

engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


# 의존성 주입용 FastAPI generator
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
