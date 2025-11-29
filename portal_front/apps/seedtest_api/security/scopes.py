from __future__ import annotations
from typing import Iterable

try:
    from fastapi import Depends, HTTPException, status
    from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
except Exception as e:  # pragma: no cover
    raise

# Minimal scope checker placeholder.
# Replace with project-specific JWKS/JWT validation.

security = HTTPBearer(auto_error=False)


def require_scope(required: Iterable[str]):
    req = set(required)

    def _dep(creds: HTTPAuthorizationCredentials = Depends(security)) -> None:
        if not creds:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="missing credentials")
        token = creds.credentials or ""
        # naive parse: scopes in a dummy header or token placeholder
        # In real project, decode JWT and extract 'scope' or 'scopes'
        scopes = set()
        # e.g., from env or request context; here treated as empty
        if not (scopes & req):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="insufficient_scope")
    return _dep
