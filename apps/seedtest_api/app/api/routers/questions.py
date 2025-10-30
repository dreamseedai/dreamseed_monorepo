"""Re-export the questions router under proposed path.

Allows imports from apps.seedtest_api.app.api.routers.questions:router
"""

from ....routers.questions import router  # type: ignore[F401]

__all__ = ["router"]
