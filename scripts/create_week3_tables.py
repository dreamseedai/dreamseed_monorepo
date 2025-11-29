"""
Week 3 Exam Flow - Database Schema Setup

Since alembic env.py is missing in backend/alembic/, this script manually creates
the Week 3 exam flow tables using SQLAlchemy's create_all().

Tables created:
- exams
- items
- item_options
- exam_items
- exam_sessions
- exam_session_responses

Usage:
  python scripts/create_week3_tables.py
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from sqlalchemy.ext.asyncio import create_async_engine
from app.core.database import Base  # type: ignore[import-not-found]
from app.models.exam_models import (  # type: ignore[import-not-found]
    Exam,
    Item,
    ItemOption,
    ExamItem,
    ExamSession,
    ExamSessionResponse,
)

# Explicitly reference imports to satisfy linters (needed for SQLAlchemy metadata)
_ = (Exam, Item, ItemOption, ExamItem, ExamSession, ExamSessionResponse)


async def create_tables():
    """
    Create all Week 3 exam flow tables.
    """
    # Database URL from .env or default
    DATABASE_URL = (
        "postgresql+asyncpg://dreamseed:dreamseed123@localhost:5433/dreamseed_db"
    )

    engine = create_async_engine(DATABASE_URL, echo=True)

    async with engine.begin() as conn:
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)

    await engine.dispose()
    print("\n✅ All Week 3 exam flow tables created successfully!")


if __name__ == "__main__":
    asyncio.run(create_tables())
