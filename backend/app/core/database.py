"""
Database connection for PostgreSQL
"""

import os
from typing import AsyncGenerator, Generator

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

# PostgreSQL connection string (sync)
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://postgres:DreamSeedAi0908@127.0.0.1:5432/dreamseed",
)

# PostgreSQL connection string (async) - for FastAPI-Users
ASYNC_DATABASE_URL = DATABASE_URL.replace(
    "postgresql+psycopg://", "postgresql+asyncpg://"
)

# Sync engine (for existing code)
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Async engine (for FastAPI-Users)
async_engine = create_async_engine(ASYNC_DATABASE_URL, pool_pre_ping=True)
AsyncSessionLocal = async_sessionmaker(
    async_engine, class_=AsyncSession, expire_on_commit=False
)

# Declarative base for ORM models
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency to get database session (sync)
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get async database session (for FastAPI-Users)
    """
    async with AsyncSessionLocal() as session:
        yield session


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async for session in get_async_db():
        yield session

# Alias for backward compatibility
async_session_maker = AsyncSessionLocal
