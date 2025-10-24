import os
from typing import Any, Dict, Optional

from fastapi import Cookie, Depends, HTTPException, Response, status
from itsdangerous import BadSignature, URLSafeSerializer

SESSION_COOKIE_NAME = os.getenv("PORTAL_SESSION_COOKIE", "portal_session")
SESSION_SECRET = os.getenv("PORTAL_SESSION_SECRET", "dev-secret-change-me")
SESSION_SERIALIZER = URLSafeSerializer(SESSION_SECRET, salt="portal-session")


def _serialize_session(payload: Dict[str, Any]) -> str:
    return SESSION_SERIALIZER.dumps(payload)


def _deserialize_session(token: str) -> Dict[str, Any]:
    try:
        return SESSION_SERIALIZER.loads(token)
    except BadSignature as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid session"
        ) from exc


def set_session_cookie(response: Response, payload: Dict[str, Any]) -> None:
    token = _serialize_session(payload)
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="lax",
        secure=False,
        path="/",
    )


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(SESSION_COOKIE_NAME, path="/")


def get_current_user(
    session: Optional[str] = Cookie(default=None, alias=SESSION_COOKIE_NAME)
) -> Dict[str, Any]:
    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="not authenticated"
        )
    user = _deserialize_session(session)
    if not isinstance(user, dict) or "username" not in user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid session payload"
        )
    return user
