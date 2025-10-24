from typing import Optional

from pydantic import BaseModel, EmailStr


class UserOut(BaseModel):
    id: int
    email: EmailStr


class ProfileIn(BaseModel):
    locale: Optional[str] = "en"
    country: Optional[str] = None
    grade_code: Optional[str] = None
    goal: Optional[str] = None
    subscribed: bool = False


