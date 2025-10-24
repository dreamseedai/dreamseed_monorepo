"""Re-export the exams router under proposed path.

Allows imports from apps.seedtest_api.app.api.routers.exams:router
"""
from ....routers.exams import router  # type: ignore[F401]

__all__ = ["router"]
