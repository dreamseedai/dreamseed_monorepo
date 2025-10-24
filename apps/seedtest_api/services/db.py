from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from ..settings import settings

_ENGINE: Engine | None = None
_SessionLocal: sessionmaker | None = None


def get_engine() -> Engine:
    global _ENGINE
    if _ENGINE is None:
        if not settings.DATABASE_URL:
            raise RuntimeError("DATABASE_URL is not configured")
        _ENGINE = create_engine(settings.DATABASE_URL, future=True)
    return _ENGINE


def get_session_factory() -> sessionmaker:
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(
            bind=get_engine(),
            autoflush=False,
            autocommit=False,
            future=True,
            class_=Session,
        )
    return _SessionLocal


@contextmanager
def get_session() -> Iterator[Session]:
    SessionLocal = get_session_factory()
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
