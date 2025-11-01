from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from ..settings import settings

_ENGINE: Engine | None = None
_SessionLocal: sessionmaker[Session] | None = None  # type: ignore[name-defined]


def get_engine() -> Engine:
    global _ENGINE
    if _ENGINE is None:
        if not settings.DATABASE_URL:
            # Provide a safe fallback for local/test environments to enable import-time usage
            # without requiring a real database. This is useful for unit tests that monkeypatch
            # downstream DB calls but import modules that reference the Session/engine.
            app_env = getattr(settings, "APP_ENV", "local") or "local"
            local_dev = bool(getattr(settings, "LOCAL_DEV", False))
            running_under_pytest = "PYTEST_CURRENT_TEST" in os.environ
            if app_env in {"local", "test"} or local_dev or running_under_pytest:
                _ENGINE = create_engine("sqlite:///:memory:", future=True)
            else:
                raise RuntimeError("DATABASE_URL is not configured")
        else:
            _ENGINE = create_engine(settings.DATABASE_URL, future=True)
    return _ENGINE


def get_session_factory() -> sessionmaker[Session]:
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(
            bind=get_engine(),
            autoflush=False,  # noqa: E501 (SQLAlchemy parameter name)
            autocommit=False,  # noqa: E501 (SQLAlchemy parameter name)
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
