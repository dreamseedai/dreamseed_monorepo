"""Re-export the analysis router under proposed path.

Allows imports from apps.seedtest_api.app.api.routers.analysis:router
"""
from ....routers.analysis import router  # type: ignore[F401]

__all__ = ["router"]
