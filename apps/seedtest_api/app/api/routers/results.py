"""Re-export the results router under proposed path.

Allows imports from apps.seedtest_api.app.api.routers.results:router
"""
from ....routers.results import router  # type: ignore[F401]

__all__ = ["router"]
