"""
FastAPI dependencies for authentication and database
"""
from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from uuid import UUID

from app.database import SessionLocal
from app.core.security import decode_access_token
from app.models.user import User
from app.schemas.user import TokenData


# HTTP Bearer 토큰 스키마
security = HTTPBearer()


def get_db() -> Generator:
    """
    데이터베이스 세션 의존성
    
    Yields:
        데이터베이스 세션
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    현재 인증된 사용자 가져오기
    
    Args:
        credentials: HTTP Authorization 헤더의 Bearer 토큰
        db: 데이터베이스 세션
        
    Returns:
        인증된 사용자 객체
        
    Raises:
        HTTPException: 인증 실패 시
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # 토큰 디코딩
    token = credentials.credentials
    payload = decode_access_token(token)
    
    if payload is None:
        raise credentials_exception
    
    user_id: Optional[str] = payload.get("sub")
    email: Optional[str] = payload.get("email")
    
    if user_id is None or email is None:
        raise credentials_exception
    
    # 사용자 조회
    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise credentials_exception
    
    user = db.query(User).filter(User.id == user_uuid).first()
    
    if user is None:
        raise credentials_exception
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    
    return user


def get_current_active_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    관리자 권한 확인
    
    Args:
        current_user: 현재 인증된 사용자
        
    Returns:
        관리자 사용자 객체
        
    Raises:
        HTTPException: 관리자 권한 없을 시
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user


def get_current_active_teacher(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    교사 권한 확인 (교사 또는 관리자)
    
    Args:
        current_user: 현재 인증된 사용자
        
    Returns:
        교사/관리자 사용자 객체
        
    Raises:
        HTTPException: 교사 권한 없을 시
    """
    if current_user.role not in ["teacher", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Teacher privileges required"
        )
    return current_user
