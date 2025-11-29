# app/routes/dev_alerts.py
from fastapi import APIRouter
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()

alerts = []


class Alert(BaseModel):
    level: str  # info, warning, error
    message: str


@router.post("/api/dev/alerts")
def push_alert(alert: Alert):
    alerts.append({"timestamp": datetime.now().isoformat(), **alert.dict()})
    print("🚨 Alert received:", alert.dict())
    return {"status": "ok"}


@router.get("/api/dev/alerts")
def get_alerts():
    return alerts
