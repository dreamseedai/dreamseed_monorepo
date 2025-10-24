import os
import time
from typing import Dict, cast

import httpx
from fastapi import HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt

from ..settings import Settings

_jwks = {"exp": 0, "keys": []}


async def get_jwks():
    now = int(time.time())
    if now < _jwks["exp"]:
        return _jwks["keys"]
    async with httpx.AsyncClient(timeout=3) as client:
        r = await client.get(Settings().JWKS_URL)
    r.raise_for_status()
    data = r.json()
    _jwks["keys"] = data["keys"]
    _jwks["exp"] = now + 3600
    return _jwks["keys"]


bearer = HTTPBearer(auto_error=False)


def _decode_unverified(token: str) -> Dict:
    return jwt.get_unverified_claims(token)


async def decode_token(token: str) -> Dict:
    """Decode JWT using either a static PEM public key or JWKS.

    Preference order:
    1) JWT_PUBLIC_KEY if provided
    2) JWKS_URL fallback
    """
    # Static public key path
    s = Settings()
    if getattr(s, "JWT_PUBLIC_KEY", None):
        try:
            key = cast(str, s.JWT_PUBLIC_KEY)
            return jwt.decode(
                token,
                key,  # PEM string
                audience=s.JWT_AUD,
                issuer=s.JWT_ISS,
                algorithms=["RS256"],
                options={"verify_at_hash": False},
            )
        except Exception as e:  # noqa: BLE001
            raise HTTPException(status_code=401, detail=f"Invalid token (pubkey): {e}")

    # JWKS path
    if not getattr(s, "JWKS_URL", None):
        raise HTTPException(
            status_code=500, detail="JWT configuration missing (no public key or JWKS)"
        )

    header = jwt.get_unverified_header(token)
    kid = header.get("kid")
    for key in await get_jwks():
        if key.get("kid") == kid:
            return jwt.decode(
                token,
                key,
                audience=s.JWT_AUD,
                issuer=s.JWT_ISS,
                algorithms=["RS256"],
                options={"verify_at_hash": False},
            )
    raise HTTPException(status_code=401, detail="Invalid token (kid)")


def require_scopes(*required):
    async def checker(creds: HTTPAuthorizationCredentials = Security(bearer)):
        # Runtime-friendly LOCAL_DEV check: allow env override even if settings were initialized earlier
        is_local_dev = Settings().LOCAL_DEV or (
            os.getenv("LOCAL_DEV", "false").lower() == "true"
        )
        if is_local_dev and not creds:
            return {
                "sub": "dev-user",
                "org_id": 1,
                "scope": "exam:read exam:write",
                "roles": ["student"],
            }
        if not creds:
            raise HTTPException(
                401, "Missing Authorization", headers={"WWW-Authenticate": "Bearer"}
            )
        payload = await decode_token(creds.credentials)
        token_scopes = set((payload.get("scope") or "").split())
        if not set(required).issubset(token_scopes):
            raise HTTPException(403, "insufficient_scope")
        return payload

    return checker


def same_org_guard(payload: Dict, org_id: int):
    if payload.get("roles") and "admin" in payload["roles"]:
        return
    if int(payload.get("org_id", -1)) != int(org_id):
        raise HTTPException(403, "forbidden_org")
    # EOF
