"""Session/engine helpers under proposed layout.

Bridges to existing service-level DB utilities.
"""

from contextlib import contextmanager
from typing import Generator

from sqlalchemy.orm import Session, sessionmaker

from ..services.db import get_engine, get_session, get_session_factory

# Provide a SessionLocal (sessionmaker) for frameworks/tests expecting this symbol
SessionLocal: sessionmaker = get_session_factory()


def get_db() -> Generator[Session, None, None]:
    """FastAPI-style dependency that yields a scoped Session.

    Uses the same engine/session factory as services.db to keep a single source
    of truth. Ensures the session is closed after use.
    """
    SessionFactory = get_session_factory()
    db: Session = SessionFactory()
    try:
        yield db
    finally:
        db.close()


__all__ = [
    "get_engine",
    "get_session",
    "get_session_factory",
    "SessionLocal",
    "get_db",
]
