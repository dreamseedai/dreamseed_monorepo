# common_analytics/schemas.py

from pydantic import BaseModel


class ActivityLogSchema(BaseModel):
    user_id: int
    country: str
    city: str
    latitude: float
    longitude: float
    content_type: str
    emotion: str
    duration_seconds: int


class PurchaseLogSchema(BaseModel):
    user_id: int
    package_name: str
    amount: int
    currency: str = "KRW"
    country: str
    city: str
