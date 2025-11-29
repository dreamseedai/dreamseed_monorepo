"""
Payment API for Phase 1 MVP
Mock payment system (Stripe integration in Phase 2)
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/payment", tags=["Payment"])


class SubscriptionPlan(BaseModel):
    id: str
    name: str
    price: float
    currency: str
    interval: str
    features: list[str]


class CreateCheckoutRequest(BaseModel):
    plan_id: str
    user_email: str


class CheckoutResponse(BaseModel):
    checkout_url: str
    session_id: str


class SubscriptionStatus(BaseModel):
    user_email: str
    is_active: bool
    plan_name: str | None = None
    started_at: datetime | None = None
    expires_at: datetime | None = None


# Mock in-memory subscription storage (Phase 1 MVP)
# In Phase 2: Replace with database
mock_subscriptions = {}


@router.get("/plans", response_model=list[SubscriptionPlan])
async def get_plans():
    """Get available subscription plans"""
    return [
        SubscriptionPlan(
            id="basic_monthly",
            name="Basic Monthly",
            price=10.00,
            currency="USD",
            interval="month",
            features=[
                "문제 무제한 풀이",
                "AI 피드백 (무제한)",
                "학습 진행도 추적",
                "기본 통계 및 리포트",
            ],
        ),
        SubscriptionPlan(
            id="premium_monthly",
            name="Premium Monthly",
            price=20.00,
            currency="USD",
            interval="month",
            features=[
                "모든 Basic 기능",
                "개인 맞춤형 학습 플랜",
                "고급 통계 및 분석",
                "우선 AI 피드백",
                "1:1 튜터 상담 (월 2회)",
            ],
        ),
    ]


@router.post("/checkout", response_model=CheckoutResponse)
async def create_checkout(request: CreateCheckoutRequest):
    """
    Create a checkout session (Mock for Phase 1 MVP)
    In Phase 2: Integrate with Stripe Checkout
    """
    
    # Mock checkout URL
    session_id = f"mock_session_{request.user_email}_{request.plan_id}_{datetime.now().timestamp()}"
    checkout_url = f"http://localhost:5172/payment/success?session_id={session_id}"
    
    # Store mock subscription (auto-activate in mock)
    mock_subscriptions[request.user_email] = {
        "plan_id": request.plan_id,
        "is_active": True,
        "started_at": datetime.now(),
        "expires_at": datetime.now() + timedelta(days=30),
    }
    
    logger.info(f"Mock checkout created for {request.user_email}, plan: {request.plan_id}")
    
    return CheckoutResponse(
        checkout_url=checkout_url,
        session_id=session_id,
    )


@router.get("/subscription/{user_email}", response_model=SubscriptionStatus)
async def get_subscription_status(user_email: str):
    """Check user's subscription status"""
    
    subscription = mock_subscriptions.get(user_email)
    
    if not subscription:
        return SubscriptionStatus(
            user_email=user_email,
            is_active=False,
        )
    
    # Check if expired
    is_active = subscription["expires_at"] > datetime.now()
    
    plans = await get_plans()
    plan = next((p for p in plans if p.id == subscription["plan_id"]), None)
    
    return SubscriptionStatus(
        user_email=user_email,
        is_active=is_active,
        plan_name=plan.name if plan else subscription["plan_id"],
        started_at=subscription["started_at"],
        expires_at=subscription["expires_at"],
    )


@router.post("/cancel/{user_email}")
async def cancel_subscription(user_email: str):
    """Cancel user's subscription"""
    
    if user_email not in mock_subscriptions:
        raise HTTPException(status_code=404, detail="Subscription not found")
    
    mock_subscriptions[user_email]["is_active"] = False
    
    logger.info(f"Subscription cancelled for {user_email}")
    
    return {"message": "Subscription cancelled", "user_email": user_email}


@router.get("/health")
async def payment_health():
    """Payment service health check"""
    return {
        "status": "healthy",
        "mode": "mock",
        "note": "Phase 1 MVP - Mock payment system. Stripe integration in Phase 2.",
        "active_subscriptions": len([s for s in mock_subscriptions.values() if s.get("is_active")]),
    }
