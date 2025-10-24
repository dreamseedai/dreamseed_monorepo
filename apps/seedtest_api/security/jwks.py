import time
from typing import Any, cast

import httpx
from fastapi import HTTPException, Request
from fastapi.security.utils import get_authorization_scheme_param
from jose import jwt

from ..settings import settings

_jwks_cache: dict[str, Any] | None = None
_jwks_cached_at: float = 0.0
_JWKS_TTL = 300.0  # seconds


async def _get_jwks() -> dict[str, Any]:
    global _jwks_cache, _jwks_cached_at
    now = time.time()
    if _jwks_cache and (now - _jwks_cached_at) < _JWKS_TTL:
        assert _jwks_cache is not None
        return cast(dict[str, Any], _jwks_cache)
    async with httpx.AsyncClient(timeout=5.0) as client:
        resp = await client.get(settings.JWKS_URL)
        resp.raise_for_status()
        _jwks_cache = resp.json()
        _jwks_cached_at = now
        return cast(dict[str, Any], _jwks_cache)


def _extract_token(request: Request) -> str | None:
    auth = request.headers.get("Authorization")
    scheme, param = get_authorization_scheme_param(auth)
    if scheme.lower() == "bearer" and param:
        return param
    # fallback to cookie named 'auth'
    cookie_tok = request.cookies.get('auth')
    if cookie_tok:
        return cookie_tok
    return None


async def get_current_user(request: Request):
    """JWT 검증: LOCAL_DEV=true면 통과. 아니면 JWKS로 서명/iss/aud 검증."""
    if settings.LOCAL_DEV:
        return {"sub": "local-dev"}
    token = _extract_token(request)
    if not token:
        raise HTTPException(status_code=401, detail="Missing token")

    unverified = jwt.get_unverified_header(token)
    kid = unverified.get("kid")
    jwks = await _get_jwks()
    rsa_key = None
    for key in jwks.get("keys", []):
        if key.get("kid") == kid:
            rsa_key = {
                "kty": key.get("kty"),
                "kid": key.get("kid"),
                "use": key.get("use"),
                "n": key.get("n"),
                "e": key.get("e"),
            }
            break
    if not rsa_key:
        raise HTTPException(status_code=401, detail="Invalid token (kid)")

    try:
        claims = jwt.decode(
            token,
            rsa_key,
            algorithms=[unverified.get("alg", "RS256")],
            audience=settings.JWT_AUD,
            issuer=settings.JWT_ISS,
        )
        return claims
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")
