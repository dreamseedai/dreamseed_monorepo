"""
JWT Token Issuer for Shiny Dashboard Authentication

Integrates with existing seedtest_api authentication to issue
JWT tokens that nginx/jwt-verifier can verify.

Usage:
    POST /api/auth/token with credentials
    Returns: {"access_token": "eyJ...", "token_type": "Bearer"}
"""

import os
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from jose import jwt
from pydantic import BaseModel

from ..deps import User, get_current_user
from ..settings import Settings

router = APIRouter(prefix="/auth", tags=["authentication"])


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    expires_in: int


def load_private_key() -> str:
    """Load RSA private key for JWT signing"""
    key_path = os.getenv("JWT_PRIVATE_KEY_PATH", "/etc/nginx/jwt_private.pem")
    try:
        with open(key_path, "r") as f:
            return f.read()
    except FileNotFoundError:
        raise HTTPException(
            status_code=500,
            detail=f"JWT private key not found at {key_path}. "
            "Run infra/nginx/generate_jwt_keypair.sh first.",
        )


def generate_jwt_token(
    user: User,
    expires_hours: int = 4,
) -> str:
    """
    Generate JWT token for authenticated user

    Args:
        user: Authenticated user from get_current_user dependency
        expires_hours: Token expiration time (default: 4 hours for production)

    Returns:
        Signed JWT token string
    """
    settings = Settings()
    private_key = load_private_key()

    now = datetime.now(timezone.utc)
    exp = now + timedelta(hours=expires_hours)

    # Claims matching nginx jwt_auth.lua / jwt_verifier.py expectations
    claims = {
        "sub": user.user_id,
        "user_id": user.user_id,
        "org_id": user.org_id,
        "roles": user.roles,
        "scope": user.scope or "dashboard:read dashboard:write",
        "iss": os.getenv("JWT_ISSUER", "dreamseedai"),
        "aud": os.getenv("JWT_AUDIENCE", "dashboard"),
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
    }

    token = jwt.encode(claims, private_key, algorithm="RS256")
    return token


@router.post("/token", response_model=TokenResponse)
async def issue_jwt_token(
    current_user: User = Depends(get_current_user),
    expires_hours: int = 4,
):
    """
    Issue JWT token for Shiny Dashboard access

    This endpoint assumes the user is already authenticated via existing
    seedtest_api authentication (Bearer token, session cookie, etc.).

    Returns a new JWT token that nginx can verify for dashboard access.

    Example:
        POST /api/auth/token
        Authorization: Bearer <existing-token>

        Response:
        {
          "access_token": "eyJ...",
          "token_type": "Bearer",
          "expires_in": 14400
        }

    Frontend usage:
        const response = await fetch('/api/auth/token', {
          headers: { 'Authorization': `Bearer ${existingToken}` }
        });
        const { access_token } = await response.json();
        localStorage.setItem('dashboard_token', access_token);

        // Then use for dashboard access
        window.location.href = `/admin/?token=${access_token}`;
    """
    token = generate_jwt_token(current_user, expires_hours=expires_hours)

    return TokenResponse(
        access_token=token,
        token_type="Bearer",
        expires_in=expires_hours * 3600,
    )


@router.get("/me")
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Get current authenticated user information

    Useful for debugging and verifying authentication state.
    """
    return {
        "user_id": current_user.user_id,
        "org_id": current_user.org_id,
        "roles": current_user.roles,
        "is_admin": current_user.is_admin(),
        "is_teacher": current_user.is_teacher(),
        "is_student": current_user.is_student(),
    }
