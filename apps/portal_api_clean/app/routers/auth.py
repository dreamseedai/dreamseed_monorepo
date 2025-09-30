from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db import models
from app.core.security import verify_password, hash_password, create_access_token, create_refresh_token, decode_token
from app.schemas.auth import LoginIn, RegisterIn, Token
from app.deps import get_current_user_id, get_current_user
from app.schemas.user import UserOut
from app.core.config import get_settings
from app.core.ratelimit import check_rate_limit
settings = get_settings()


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=Token)
def register(payload: RegisterIn, db: Session = Depends(get_db)):
    if db.query(models.User).filter(models.User.email == payload.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    user = models.User(email=payload.email, password_hash=hash_password(payload.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token(user.id)
    return Token(access_token=token)


@router.post("/login", response_model=Token)
async def login(payload: LoginIn, request: Request, db: Session = Depends(get_db)):
    ip = request.headers.get("x-forwarded-for") or (request.client.host if request.client else "unknown")
    bucket = f"login:{ip}:{payload.email.lower()}"
    allowed = await check_rate_limit(bucket, settings.login_rate_limit_per_min, 60)
    if not allowed:
        raise HTTPException(status_code=429, detail="Too many login attempts. Please try again later.")
    user = db.query(models.User).filter(models.User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = create_access_token(user.id)
    return Token(access_token=token)
@router.post("/login-cookie", response_model=Token)
async def login_cookie(payload: LoginIn, request: Request, response: Response, db: Session = Depends(get_db)):
    ip = request.headers.get("x-forwarded-for") or (request.client.host if request.client else "unknown")
    bucket = f"login:{ip}:{payload.email.lower()}"
    allowed = await check_rate_limit(bucket, settings.login_rate_limit_per_min, 60)
    if not allowed:
        raise HTTPException(status_code=429, detail="Too many login attempts. Please try again later.")
    user = db.query(models.User).filter(models.User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    access = create_access_token(user.id)
    refresh = create_refresh_token(user.id)
    response.set_cookie(
        key=settings.refresh_cookie_name,
        value=refresh,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        domain=settings.cookie_domain,
        max_age=settings.refresh_token_expire_minutes * 60,
        path="/",
    )
    return Token(access_token=access)

@router.post("/refresh", response_model=Token)
def refresh_token(request: Request, response: Response, db: Session = Depends(get_db)):
    rt = request.cookies.get(settings.refresh_cookie_name)
    if not rt:
        raise HTTPException(status_code=401, detail="No refresh token")
    try:
        payload = decode_token(rt)
        if payload.get("typ") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid refresh token")
        uid = int(payload["sub"])
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    user = db.get(models.User, uid)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    access = create_access_token(uid)
    return Token(access_token=access)

@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(
        key=settings.refresh_cookie_name,
        domain=settings.cookie_domain,
        path="/",
    )
    return {"ok": True}

@router.get("/me", response_model=UserOut)
def me(user = Depends(get_current_user)):
    return UserOut(id=user.id, email=user.email)
