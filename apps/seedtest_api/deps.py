from __future__ import annotations

import os
from typing import List, Optional

from fastapi import Depends, HTTPException, Security
from pydantic import BaseModel
from sqlalchemy import text

from .security.jwt import bearer, decode_token
from .services.adaptive_engine import get_session_state
from .services.db import get_session as _db_get_session
from .services.result_service import get_result_from_db
from .settings import Settings
from .app.clients.r_plumber import RPlumberClient
from .app.clients.r_irt import RIRTClient


class User(BaseModel):
    user_id: str
    org_id: Optional[int] = None
    roles: List[str] = []
    scope: Optional[str] = None

    def is_admin(self) -> bool:
        return any(r.lower() == "admin" for r in self.roles)

    def is_teacher(self) -> bool:
        return any(r.lower() == "teacher" for r in self.roles)

    def is_student(self) -> bool:
        return any(r.lower() == "student" for r in self.roles) or not (
            self.is_admin() or self.is_teacher()
        )


async def get_current_user(creds=Security(bearer)) -> User:
    # Allow LOCAL_DEV without header
    s = Settings()
    if (s.LOCAL_DEV or os.getenv("LOCAL_DEV", "false").lower() == "true") and not creds:
        # Allow overriding roles via env for local development (e.g., LOCAL_DEV_ROLES="teacher admin")
        roles_env = os.getenv("LOCAL_DEV_ROLES", "teacher")
        roles = [r for r in (roles_env.split() if roles_env else []) if r]
        return User(
            user_id="dev-user",
            org_id=1,
            roles=roles or ["teacher"],
            scope="exam:read exam:write",
        )
    if not creds:
        raise HTTPException(
            status_code=401,
            detail="Missing Authorization",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = await decode_token(creds.credentials)
    sub = str(payload.get("sub") or payload.get("user_id") or "").strip()
    if not sub:
        raise HTTPException(401, "invalid_token_subject")
    roles = payload.get("roles") or []
    if isinstance(roles, str):
        roles = [r for r in roles.split() if r]
    org_id = payload.get("org_id")
    try:
        org_id = int(org_id) if org_id is not None else None
    except Exception:
        org_id = None
    scope = payload.get("scope")
    return User(user_id=sub, org_id=org_id, roles=[str(r) for r in roles], scope=scope)


def require_session_access(
    session_id: str,
    current_user: User = Depends(get_current_user),
):
    """Authorize access to a given session_id based on user role and org.

    - admin: always allowed
    - teacher: allowed if org_id matches session's org_id (from session state)
    - student: only allowed if owns the session

    In absence of session state, falls back to DB result ownership check (student only).
    """
    # Allow everything in LOCAL_DEV to keep developer ergonomics and tests green
    s = Settings()
    if s.LOCAL_DEV or os.getenv("LOCAL_DEV", "false").lower() == "true":
        return

    # Admins can access anything
    if current_user.is_admin():
        return

    # Try to read in-memory session state (when the session is still active in adaptive engine)
    state = get_session_state(session_id)
    if state:
        # Student: must match user_id
        if current_user.is_student():
            if str(state.get("user_id")) != current_user.user_id:
                raise HTTPException(403, "Permission denied")
            return
        # Teacher: same org policy
        if current_user.is_teacher():
            sess_org = state.get("org_id")
            if (
                (sess_org is None)
                or (current_user.org_id is None)
                or int(sess_org) != int(current_user.org_id)
            ):
                raise HTTPException(403, "Permission denied")
            return

    # Fallback (1): DB session lookup for ownership/org checks when in-memory state is absent
    try:
        with _db_get_session() as s:
            row = (
                s.execute(
                    text(
                        """
                        SELECT user_id, org_id
                        FROM exam_sessions
                        WHERE session_id = :sid
                        """
                    ),
                    {"sid": session_id},
                )
                .mappings()
                .first()
            )
            if row is not None:
                sess_user = str(row.get("user_id") or "")
                sess_org = row.get("org_id")
                # Student: must match user_id
                if current_user.is_student():
                    if sess_user and sess_user == current_user.user_id:
                        return
                    raise HTTPException(403, "Permission denied")
                # Teacher: org must match (admin was already handled above)
                if current_user.is_teacher():
                    try:
                        if (
                            current_user.org_id is not None
                            and sess_org is not None
                            and int(current_user.org_id) == int(sess_org)
                        ):
                            return
                    except Exception:
                        pass
                    raise HTTPException(403, "Permission denied")
                # Non-student/teacher (unknown role): deny
                raise HTTPException(403, "Permission denied")
    except Exception:
        # If DB not configured or table missing, continue to legacy fallback
        pass

    # Fallback (2): DB result ownership when available (student only)
    if current_user.is_student():
        row = get_result_from_db(
            session_id=session_id, expected_user_id=current_user.user_id
        )
        if row is None:
            # Unknown or not owned
            raise HTTPException(403, "Permission denied")
        return

    # Teachers without state cannot be verified by org here (no org on results row);
    # keep conservative and deny to avoid data leak.
    if current_user.is_teacher():
        raise HTTPException(403, "Permission denied")

    # Not found anywhere
    raise HTTPException(404, "Session not found")


def get_r_plumber_client() -> RPlumberClient:
    """Build an R Plumber client from environment/settings.

    Resolution order:
    - Settings.R_PLUMBER_BASE_URL when provided
    - If LOCAL_DEV true, default to http://127.0.0.1:8000 for developer ergonomics
    - Else 503 to indicate misconfiguration
    """
    s = Settings()
    base = s.R_PLUMBER_BASE_URL
    if not base and (s.LOCAL_DEV or os.getenv("LOCAL_DEV", "false").lower() == "true"):
        base = "http://127.0.0.1:8000"
    if not base:
        raise HTTPException(status_code=503, detail="r_plumber_unconfigured")
    return RPlumberClient(
        base_url=base,
        timeout=float(s.R_PLUMBER_TIMEOUT_SECS),
        internal_token=s.R_PLUMBER_INTERNAL_TOKEN,
    )


def get_r_irt_client() -> RIRTClient:
    """Build an R IRT Plumber client from environment/settings.

    Resolution order:
    - Settings.R_IRT_BASE_URL when provided
    - If LOCAL_DEV true, default to http://127.0.0.1:8000 for developer ergonomics
    - Else 503 to indicate misconfiguration
    """
    s = Settings()
    base = s.R_IRT_BASE_URL
    if not base and (s.LOCAL_DEV or os.getenv("LOCAL_DEV", "false").lower() == "true"):
        base = "http://127.0.0.1:8000"
    if not base:
        raise HTTPException(status_code=503, detail="r_irt_unconfigured")
    return RIRTClient(
        base_url=base,
        timeout=float(s.R_IRT_TIMEOUT_SECS),
        internal_token=s.R_IRT_INTERNAL_TOKEN,
    )
