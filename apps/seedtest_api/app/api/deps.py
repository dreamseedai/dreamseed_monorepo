"""Auth/permission dependencies (shim over existing security module).

This aligns with the proposed structure while delegating to the existing
security implementation in seedtest_api.security.jwt.
"""

from typing import Callable, Dict

from fastapi import Depends, HTTPException

from ...security.jwt import require_scopes
from ...settings import settings
from ..clients.r_plumber import RPlumberClient


async def get_current_user(user: Dict = Depends(require_scopes("exam:read"))) -> Dict:
    """Return the authenticated user payload (JWT claims) using exam:read as baseline.

    Adjust required scopes per endpoint as needed by calling require_scopes directly.
    """
    return user


def require_session_access(session_owner_id_getter: Callable[[str], str | None]):
    """Factory returning a dependency to check session access.

    session_owner_id_getter: function that maps session_id -> user_id (owner)
    For initial version, allow access if user is admin/teacher or owns the session.
    """

    async def _checker(
        session_id: str, user: Dict = Depends(require_scopes("exam:read"))
    ):
        roles = set(user.get("roles", []) or [])
        if "admin" in roles or "teacher" in roles:
            return user
        owner = session_owner_id_getter(session_id)
        if owner and str(owner) == str(user.get("sub")):
            return user
        raise HTTPException(403, "forbidden_session")

    return _checker


__all__ = ["get_current_user", "require_session_access", "require_scopes"]


def get_r_plumber_client() -> RPlumberClient:
    """Provide an RPlumberClient using workspace settings.

    Resolution order:
    - If settings.R_PLUMBER_BASE_URL is set, use it.
    - Else if LOCAL_DEV, default to http://127.0.0.1:8000 for convenience.
    - Else raise 503 to signal the dependency is not configured.
    """
    base = settings.R_PLUMBER_BASE_URL
    if not base and settings.LOCAL_DEV:
        base = "http://127.0.0.1:8000"
    if not base:
        raise HTTPException(status_code=503, detail="r_plumber_unconfigured")
    return RPlumberClient(
        base_url=base,
        timeout=settings.R_PLUMBER_TIMEOUT_SECS,
        internal_token=settings.R_PLUMBER_INTERNAL_TOKEN,
    )

