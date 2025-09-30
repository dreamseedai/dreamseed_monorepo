from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
import stripe
from datetime import date
import hashlib
from app.core.config import get_settings
from app.db.session import get_db
from app.deps import get_current_user, require_roles
from fastapi import Query
from typing import cast
from datetime import datetime, timezone, timedelta
from app.db import models


router = APIRouter(prefix="/billing/stripe", tags=["billing"])


settings = get_settings()

def _ensure_stripe() -> None:
    if not settings.stripe_secret_key or not settings.stripe_price_id:
        raise HTTPException(status_code=500, detail="Stripe not configured")
    stripe.api_key = settings.stripe_secret_key

_PROCESSED_EVENTS: set[str] = set()

def _idempotency_key(user_id: int) -> str:
    raw = f"checkout:{user_id}:{settings.stripe_price_id}:{date.today().isoformat()}"
    return hashlib.sha256(raw.encode()).hexdigest()[:32]


@router.post("/create-checkout-session")
def create_checkout_session(db: Session = Depends(get_db), user=Depends(get_current_user)):
    _ensure_stripe()
    if not user.email:
        raise HTTPException(status_code=400, detail="User email required")
    idem = _idempotency_key(user.id)
    # assure type expectations
    price_id: str = settings.stripe_price_id or ""
    success_url: str = settings.stripe_success_url or "http://127.0.0.1:5172/success"
    cancel_url: str = settings.stripe_cancel_url or "http://127.0.0.1:5172/cancel"

    session = stripe.checkout.Session.create(
        mode="subscription",
        payment_method_types=["card"],
        line_items=[{"price": price_id, "quantity": 1}],
        customer_email=user.email,
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={"user_id": str(user.id), "env": settings.app_env},
        idempotency_key=idem,
    )
    return {"id": session.id, "url": session.url, "idem": idem}


@router.post("/webhook")
async def webhook(request: Request, db: Session = Depends(get_db)):
    _ensure_stripe()
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    if not settings.stripe_webhook_secret:
        raise HTTPException(status_code=500, detail="Webhook secret not configured")
    try:
        event = stripe.Webhook.construct_event(
            payload=payload, sig_header=sig_header, secret=settings.stripe_webhook_secret
        )
    except Exception as e:  # noqa: BLE001 - we want to surface any stripe error
        raise HTTPException(status_code=400, detail=f"Webhook error: {e}")

    evt_id = event.get("id")
    if evt_id in _PROCESSED_EVENTS:
        return {"ok": True, "dedup": True}
    _PROCESSED_EVENTS.add(str(evt_id))

    etype = event.get("type") or ""
    obj = event.get("data", {}).get("object", {}) or {}
    user_id = (obj.get("metadata") or {}).get("user_id")

    # extended fields
    customer_id = obj.get("customer") or obj.get("customer_id")
    subscription_id = obj.get("subscription") if isinstance(obj.get("subscription"), str) else None
    amount_total = obj.get("amount_total")
    currency = obj.get("currency")
    livemode = bool(event.get("livemode", False))
    status = obj.get("status") or obj.get("payment_status")
    req = event.get("request") or {}
    request_id = req.get("id") if isinstance(req, dict) else None
    idem_key = obj.get("idempotency_key") or (req.get("idempotency_key") if isinstance(req, dict) else None)

    # persist event row for dedup and audit
    try:
        rec = models.StripeWebhookEvent(
            event_id=evt_id,
            event_type=etype,
            payload=event,
            processed=False,
            customer_id=customer_id,
            subscription_id=subscription_id,
            idempotency_key=idem_key,
            request_id=request_id,
            amount_total=(amount_total / 100.0 if isinstance(amount_total, int) else amount_total),
            currency=currency,
            livemode=livemode,
            status=status,
        )
        db.add(rec)
        db.commit()
        db.refresh(rec)
    except Exception:
        db.rollback()
        return {"ok": True, "dedup": True}

    if etype in ("checkout.session.completed", "invoice.payment_succeeded", "customer.subscription.updated", "customer.subscription.created"):
        if user_id:
            u = db.get(models.User, int(user_id))
            if u:
                prof = db.query(models.UserProfile).filter(models.UserProfile.user_id == u.id).first()
                if not prof:
                    prof = models.UserProfile(user_id=u.id, subscribed=True)
                    db.add(prof)
                else:
                    prof.subscribed = True
                # map customer/subscription/status
                if obj.get("customer") or obj.get("customer_id"):
                    prof.stripe_customer_id = obj.get("customer") or obj.get("customer_id")
                sub_id = obj.get("subscription") if isinstance(obj.get("subscription"), str) else (obj.get("id") if etype.startswith("customer.subscription") else None)
                if sub_id:
                    prof.stripe_subscription_id = sub_id
                status = obj.get("status") or obj.get("payment_status")
                if status:
                    prof.status = status
                cpe = obj.get("current_period_end")
                if isinstance(cpe, int):
                    from datetime import datetime, timezone
                    prof.current_period_end = datetime.fromtimestamp(cpe, tz=timezone.utc)
                cape = obj.get("cancel_at_period_end")
                if isinstance(cape, bool):
                    prof.cancel_at_period_end = cape
                db.commit()
    elif etype in ("customer.subscription.deleted", "invoice.payment_failed"):
        if user_id:
            u = db.get(models.User, int(user_id))
            if u:
                prof = db.query(models.UserProfile).filter(models.UserProfile.user_id == u.id).first()
                if prof:
                    prof.subscribed = False
                    if etype == "customer.subscription.deleted":
                        prof.status = "canceled"
                    db.commit()
    # mark processed
    try:
        db.query(models.StripeWebhookEvent).filter(models.StripeWebhookEvent.event_id == evt_id).update({"processed": True})
        db.commit()
    except Exception:
        db.rollback()
    return {"ok": True}


@router.get("/status")
def billing_status(user=Depends(get_current_user), db: Session = Depends(get_db)):
    prof = db.query(models.UserProfile).filter(models.UserProfile.user_id == user.id).first()
    return {
        "subscribed": bool(prof and prof.subscribed),
        "status": getattr(prof, "status", None) if prof else None,
        "current_period_end": getattr(prof, "current_period_end", None) if prof else None,
        "cancel_at_period_end": getattr(prof, "cancel_at_period_end", None) if prof else None,
        "customer_id": getattr(prof, "stripe_customer_id", None) if prof else None,
        "subscription_id": getattr(prof, "stripe_subscription_id", None) if prof else None,
    }


@router.get("/expiring")
def list_expiring_subscriptions(
    days: int = Query(3, ge=1, le=30),
    limit: int = Query(200, ge=1, le=1000),
    db: Session = Depends(get_db),
    admin=Depends(require_roles("admin")),
):
    now = datetime.now(timezone.utc)
    until = now + timedelta(days=days)
    q = (
        db.query(models.User, models.UserProfile)
        .join(models.UserProfile, models.UserProfile.user_id == models.User.id)
        .filter(models.UserProfile.subscribed.is_(True))
        .filter(models.UserProfile.current_period_end.isnot(None))
        .filter(models.UserProfile.current_period_end <= until)
        .order_by(models.UserProfile.current_period_end.asc())
        .limit(limit)
    )
    rows = q.all()
    out = []
    for u, p in rows:
        days_left = None
        if p.current_period_end:
            delta = p.current_period_end - now
            days_left = max(0, int(delta.total_seconds() // 86400))
        out.append({
            "user_id": u.id,
            "email": u.email,
            "status": p.status,
            "current_period_end": p.current_period_end,
            "cancel_at_period_end": p.cancel_at_period_end,
            "days_left": days_left,
            "subscription_id": p.stripe_subscription_id,
            "customer_id": p.stripe_customer_id,
        })
    return {"items": out, "count": len(out), "days": days}


@router.post("/sync-one")
def sync_one(
    user_id: int = Query(..., ge=1),
    db: Session = Depends(get_db),
    admin=Depends(require_roles("admin")),
):
    _ensure_stripe()
    u = db.get(models.User, user_id)
    if not u:
        raise HTTPException(404, "User not found")
    p = db.query(models.UserProfile).filter(models.UserProfile.user_id == user_id).first()
    if not p or not p.stripe_subscription_id:
        raise HTTPException(400, "No subscription on file")
    s_id: str = cast(str, p.stripe_subscription_id)
    sub = stripe.Subscription.retrieve(s_id)
    p.status = sub.get("status")
    cpe = sub.get("current_period_end")
    if isinstance(cpe, int):
        p.current_period_end = datetime.fromtimestamp(cpe, tz=timezone.utc)
    cape = sub.get("cancel_at_period_end")
    if isinstance(cape, bool):
        p.cancel_at_period_end = cape
    cust = sub.get("customer")
    if isinstance(cust, str):
        p.stripe_customer_id = cust
    p.subscribed = p.status in ("active", "trialing") and not p.cancel_at_period_end
    db.commit()
    return {"ok": True, "user_id": user_id, "status": p.status, "current_period_end": p.current_period_end}


@router.post("/sync-all")
def sync_all(
    limit: int = Query(200, ge=1, le=1000),
    db: Session = Depends(get_db),
    admin=Depends(require_roles("admin")),
):
    _ensure_stripe()
    profs = (
        db.query(models.UserProfile)
        .filter(models.UserProfile.stripe_subscription_id.isnot(None))
        .order_by(models.UserProfile.user_id.asc())
        .limit(limit)
        .all()
    )
    updated = 0
    for p in profs:
        try:
            s_id2: str = cast(str, p.stripe_subscription_id)
            sub = stripe.Subscription.retrieve(s_id2)
            p.status = sub.get("status")
            cpe = sub.get("current_period_end")
            if isinstance(cpe, int):
                p.current_period_end = datetime.fromtimestamp(cpe, tz=timezone.utc)
            cape = sub.get("cancel_at_period_end")
            if isinstance(cape, bool):
                p.cancel_at_period_end = cape
            cust = sub.get("customer")
            if isinstance(cust, str):
                p.stripe_customer_id = cust
            p.subscribed = p.status in ("active", "trialing") and not p.cancel_at_period_end
            updated += 1
        except Exception:
            db.rollback()
        else:
            db.commit()
    return {"ok": True, "updated": updated}



@router.get("/events")
def list_events(
    limit: int = Query(50, ge=1, le=200),
    after_id: int | None = None,
    event_type: str | None = None,
    processed: bool | None = None,
    db: Session = Depends(get_db),
    admin = Depends(require_roles("admin")),
):
    q = db.query(models.StripeWebhookEvent).order_by(models.StripeWebhookEvent.id.desc())
    if after_id:
        q = q.filter(models.StripeWebhookEvent.id < after_id)
    if event_type:
        q = q.filter(models.StripeWebhookEvent.event_type == event_type)
    if processed is not None:
        q = q.filter(models.StripeWebhookEvent.processed == processed)
    rows = q.limit(limit).all()
    return [
        {
            "id": r.id,
            "event_id": r.event_id,
            "event_type": r.event_type,
            "received_at": r.received_at,
            "processed": r.processed,
            "status": r.status,
            "customer_id": r.customer_id,
            "subscription_id": r.subscription_id,
            "amount_total": (str(r.amount_total) if r.amount_total is not None else None),
            "currency": r.currency,
            "livemode": r.livemode,
            "idempotency_key": r.idempotency_key,
            "request_id": r.request_id,
        }
        for r in rows
    ]
