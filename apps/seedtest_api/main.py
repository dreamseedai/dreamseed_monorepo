"""Legacy entrypoint kept for backward compatibility.

This module now re-exports the FastAPI app from the proposed structure at
`apps.seedtest_api.app.main`. Keep imports stable for callers depending on
`seedtest_api.main:app`.
"""

from .app.main import app  # re-export single source of truth

__all__ = ["app"]
