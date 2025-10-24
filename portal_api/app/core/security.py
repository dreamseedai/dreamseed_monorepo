from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from app.core.config import get_settings
from jose import jwt
from passlib.context import CryptContext

settings = get_settings()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)

def _utcnow():
    return datetime.now(timezone.utc)

def create_access_token(subject: str | int, expires_minutes: int | None = None) -> str:
    if expires_minutes is None:
        expires_minutes = settings.access_token_expire_minutes
    expire = _utcnow() + timedelta(minutes=expires_minutes)
    to_encode: dict[str, Any] = {"sub": str(subject), "exp": expire}
    return jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_alg)

def create_refresh_token(subject: str | int, expires_minutes: int | None = None) -> str:
    if expires_minutes is None:
        expires_minutes = settings.refresh_token_expire_minutes
    expire = _utcnow() + timedelta(minutes=expires_minutes)
    to_encode: dict[str, Any] = {"sub": str(subject), "exp": expire, "typ": "refresh"}
    return jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_alg)

def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_alg])


