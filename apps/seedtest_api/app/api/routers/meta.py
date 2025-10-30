"""Re-export the meta router under proposed path.

Allows imports from apps.seedtest_api.app.api.routers.meta:router
"""

from ....routers.meta import router  # type: ignore[F401]

__all__ = ["router"]
