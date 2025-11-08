"""Database session management for shared modules.

Provides database connection and session management utilities that can be
used across different parts of the application.
"""

from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

# Global engine and session factory
_ENGINE: Engine | None = None
_SessionLocal: sessionmaker[Session] | None = None


def get_engine(database_url: str | None = None) -> Engine:
    """Get or create the SQLAlchemy engine.
    
    Args:
        database_url: Optional database URL. If not provided, uses environment variable.
        
    Returns:
        SQLAlchemy Engine instance
    """
    global _ENGINE
    if _ENGINE is None:
        if database_url is None:
            import os
            database_url = os.getenv("DATABASE_URL")
            
        if not database_url:
            # Fallback for local/test environments
            if os.getenv("PYTEST_CURRENT_TEST") or os.getenv("APP_ENV") in {"local", "test"}:
                _ENGINE = create_engine("sqlite:///:memory:", future=True)
            else:
                raise RuntimeError("DATABASE_URL is not configured")
        else:
            _ENGINE = create_engine(database_url, future=True)
    return _ENGINE


def get_session_factory(database_url: str | None = None) -> sessionmaker[Session]:
    """Get or create the session factory.
    
    Args:
        database_url: Optional database URL to initialize the engine.
        
    Returns:
        SQLAlchemy sessionmaker instance
    """
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(
            bind=get_engine(database_url),
            autoflush=False,
            autocommit=False,
            class_=Session,
        )
    return _SessionLocal


@contextmanager
def get_session(database_url: str | None = None) -> Generator[Session, None, None]:
    """Context manager that provides a database session.
    
    Usage:
        with get_session() as session:
            # Use session here
            pass
    
    Args:
        database_url: Optional database URL.
        
    Yields:
        SQLAlchemy Session instance
    """
    SessionLocal = get_session_factory(database_url)
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_db(database_url: str | None = None) -> Generator[Session, None, None]:
    """FastAPI dependency for database sessions.
    
    Usage:
        @app.get("/items")
        def read_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    
    Args:
        database_url: Optional database URL.
        
    Yields:
        SQLAlchemy Session instance
    """
    SessionFactory = get_session_factory(database_url)
    db: Session = SessionFactory()
    try:
        yield db
    finally:
        db.close()


__all__ = [
    "get_engine",
    "get_session",
    "get_session_factory",
    "get_db",
]
