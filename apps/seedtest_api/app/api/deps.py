"""Auth/permission dependencies (shim over existing security module).

This aligns with the proposed structure while delegating to the existing
security implementation in seedtest_api.security.jwt.
"""

from typing import Callable, Dict

from fastapi import Depends, HTTPException

from ...security.jwt import require_scopes


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
