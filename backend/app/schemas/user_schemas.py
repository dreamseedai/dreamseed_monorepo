"""
User schemas for authentication and user management
"""
from typing import Optional
from pydantic import BaseModel, EmailStr, ConfigDict
from fastapi_users import schemas


class UserRead(schemas.BaseUser[int]):
    """User read schema - returned to client"""
    model_config = ConfigDict(from_attributes=True)
    
    full_name: Optional[str] = None
    role: str


class UserCreate(schemas.BaseUserCreate):
    """User creation schema - for registration"""
    full_name: Optional[str] = None
    role: Optional[str] = "student"  # Default to student


class UserUpdate(schemas.BaseUserUpdate):
    """User update schema"""
    full_name: Optional[str] = None
