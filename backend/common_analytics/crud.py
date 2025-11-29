# common_analytics/crud.py

from sqlalchemy.orm import Session
from common_analytics.models import UserActivityLog, UserPurchaseLog
from common_analytics.schemas import ActivityLogSchema, PurchaseLogSchema


def save_activity_log(db: Session, data: ActivityLogSchema):
    log = UserActivityLog(**data.dict())
    db.add(log)
    db.commit()
    return log.id


def save_purchase_log(db: Session, data: PurchaseLogSchema):
    log = UserPurchaseLog(**data.dict())
    db.add(log)
    db.commit()
    return log.id
