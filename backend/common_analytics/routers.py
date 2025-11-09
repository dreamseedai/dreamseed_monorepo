# common_analytics/routers.py

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from common_analytics.schemas import ActivityLogSchema, PurchaseLogSchema
from common_analytics.crud import save_activity_log, save_purchase_log

analytics_router = APIRouter(prefix="/analytics", tags=["Analytics"])


@analytics_router.post("/log/activity")
def log_activity(data: ActivityLogSchema, db: Session = Depends(get_db)):
    log_id = save_activity_log(db, data)
    return {"status": "success", "log_id": log_id}


@analytics_router.post("/log/purchase")
def log_purchase(data: PurchaseLogSchema, db: Session = Depends(get_db)):
    log_id = save_purchase_log(db, data)
    return {"status": "success", "log_id": log_id}
