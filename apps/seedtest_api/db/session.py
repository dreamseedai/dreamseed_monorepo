"""Session/engine helpers under proposed layout.

Bridges to existing service-level DB utilities.
"""
from sqlalchemy.orm import sessionmaker

from ..services.db import get_engine, get_session, get_session_factory

# Provide a SessionLocal (sessionmaker) for frameworks/tests expecting this symbol
SessionLocal: sessionmaker = get_session_factory()

__all__ = ["get_engine", "get_session", "get_session_factory", "SessionLocal"]
