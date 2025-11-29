"""
Pydantic schemas for User-related requests and responses
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from uuid import UUID


class UserBase(BaseModel):
    """사용자 기본 스키마"""
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=100)
    role: str = Field(default="student", pattern="^(student|parent|teacher|admin)$")


class UserCreate(UserBase):
    """사용자 생성 요청"""
    password: str = Field(..., min_length=8, max_length=100)


class UserUpdate(BaseModel):
    """사용자 정보 수정"""
    full_name: Optional[str] = Field(None, min_length=1, max_length=100)
    password: Optional[str] = Field(None, min_length=8, max_length=100)


class UserResponse(UserBase):
    """사용자 응답"""
    id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    """로그인 요청"""
    email: EmailStr
    password: str


class Token(BaseModel):
    """JWT 토큰 응답"""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """토큰 페이로드 데이터"""
    user_id: Optional[UUID] = None
    email: Optional[str] = None
    role: Optional[str] = None
