"""
User schemas for authentication and user management
"""

import re
from typing import Optional

from fastapi_users import schemas
from pydantic import BaseModel, ConfigDict, EmailStr, field_validator


class UserRead(schemas.BaseUser[int]):
    """User read schema - returned to client"""

    model_config = ConfigDict(from_attributes=True)

    full_name: Optional[str] = None
    role: str


class UserCreate(schemas.BaseUserCreate):
    """User creation schema - for registration"""

    full_name: Optional[str] = None
    role: Optional[str] = "student"  # Default to student

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """
        Validate password complexity according to OWASP guidelines.

        Requirements:
        - Minimum 10 characters
        - At least 3 out of 4 character types:
          * Uppercase letters (A-Z)
          * Lowercase letters (a-z)
          * Digits (0-9)
          * Special characters (!@#$%^&*()_+-=[]{}|;:,.<>?)

        Args:
            v: Password string to validate

        Returns:
            str: Validated password

        Raises:
            ValueError: If password doesn't meet requirements
        """
        if len(v) < 10:
            raise ValueError("Password must be at least 10 characters long")

        # Count character type categories
        categories = 0
        if re.search(r"[A-Z]", v):
            categories += 1  # Uppercase
        if re.search(r"[a-z]", v):
            categories += 1  # Lowercase
        if re.search(r"\d", v):
            categories += 1  # Digits
        if re.search(r"[^A-Za-z0-9]", v):
            categories += 1  # Special characters

        if categories < 3:
            raise ValueError(
                "Password must contain at least 3 of the following: "
                "uppercase letters, lowercase letters, digits, special characters"
            )

        return v


class UserUpdate(schemas.BaseUserUpdate):
    """User update schema"""

    full_name: Optional[str] = None
