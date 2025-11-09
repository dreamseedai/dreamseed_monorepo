# Stripe Payment Integration

## Table of Contents

- [Overview](#overview)
- [Subscription Models](#subscription-models)
- [Stripe Architecture](#stripe-architecture)
- [Checkout Flow](#checkout-flow)
- [Webhook Processing](#webhook-processing)
- [License Management](#license-management)
- [Implementation](#implementation)
- [Testing Strategy](#testing-strategy)

## Overview

Payment processing with Stripe handles:

- **Individual subscriptions**: Monthly/annual plans for students/teachers
- **School licenses**: Seat-based pricing (10-1000 seats)
- **Usage tracking**: Active seat assignments per license
- **Billing management**: Upgrades, downgrades, prorations, cancellations
- **Compliance**: PCI-DSS Level 1 (Stripe handles card data)

**Stripe Products**: Checkout, Billing, Customer Portal, Webhooks

## Subscription Models

### Pricing Tiers

| Plan | Type | Price | Features |
|------|------|-------|----------|
| Student | Individual | $9.99/month | Unlimited assessments, AI tutor, reports |
| Teacher | Individual | $29.99/month | Student plan + Class management, analytics |
| School Starter | License (10-50 seats) | $19.99/seat/month | All features + LTI integration |
| School Pro | License (51-200 seats) | $14.99/seat/month | School Starter + Priority support |
| School Enterprise | License (201+ seats) | Custom pricing | School Pro + SLA, custom integration |

### Database Schema

```sql
-- Stripe customers
CREATE TABLE stripe_customers (
    customer_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(organization_id),
    stripe_customer_id VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_stripe_customers_org ON stripe_customers(organization_id);
CREATE INDEX idx_stripe_customers_stripe_id ON stripe_customers(stripe_customer_id);

-- Subscriptions
CREATE TABLE subscriptions (
    subscription_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(organization_id),
    stripe_subscription_id VARCHAR(100) UNIQUE NOT NULL,
    stripe_customer_id VARCHAR(100) NOT NULL,
    plan_type VARCHAR(50) NOT NULL,  -- student, teacher, school_starter, school_pro
    status VARCHAR(50) NOT NULL,  -- active, past_due, canceled, incomplete
    current_period_start TIMESTAMPTZ,
    current_period_end TIMESTAMPTZ,
    cancel_at_period_end BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_subscriptions_org ON subscriptions(organization_id);
CREATE INDEX idx_subscriptions_stripe_id ON subscriptions(stripe_subscription_id);
CREATE INDEX idx_subscriptions_status ON subscriptions(status);

-- School licenses (for seat-based plans)
CREATE TABLE school_licenses (
    license_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subscription_id UUID NOT NULL REFERENCES subscriptions(subscription_id) ON DELETE CASCADE,
    organization_id UUID NOT NULL REFERENCES organizations(organization_id),
    total_seats INT NOT NULL,
    seats_assigned INT DEFAULT 0,
    seats_available INT GENERATED ALWAYS AS (total_seats - seats_assigned) STORED,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT seats_valid CHECK (seats_assigned <= total_seats)
);

CREATE INDEX idx_licenses_org ON school_licenses(organization_id);
CREATE INDEX idx_licenses_subscription ON school_licenses(subscription_id);

-- Seat assignments
CREATE TABLE license_seat_assignments (
    assignment_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    license_id UUID NOT NULL REFERENCES school_licenses(license_id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    assigned_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    revoked_at TIMESTAMPTZ,
    UNIQUE(license_id, user_id)
);

CREATE INDEX idx_seat_assignments_license ON license_seat_assignments(license_id);
CREATE INDEX idx_seat_assignments_user ON license_seat_assignments(user_id);
CREATE INDEX idx_seat_assignments_active ON license_seat_assignments(license_id) WHERE revoked_at IS NULL;
```

## Stripe Architecture

### Service Layer

```python
# app/services/stripe_service.py
import stripe
from typing import Dict, Optional
from uuid import UUID
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings

stripe.api_key = settings.STRIPE_SECRET_KEY

class StripeService:
    """Stripe payment service."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_customer(
        self,
        organization_id: UUID,
        email: str,
        metadata: Optional[Dict] = None
    ) -> str:
        """Create Stripe customer."""
        customer = stripe.Customer.create(
            email=email,
            metadata={
                "organization_id": str(organization_id),
                **(metadata or {})
            }
        )
        
        # Save to database
        query = text("""
            INSERT INTO stripe_customers (organization_id, stripe_customer_id, email)
            VALUES (:org_id, :stripe_id, :email)
            RETURNING customer_id
        """)
        
        await self.db.execute(query, {
            "org_id": str(organization_id),
            "stripe_id": customer.id,
            "email": email
        })
        await self.db.commit()
        
        return customer.id
    
    async def create_checkout_session(
        self,
        customer_id: str,
        price_id: str,
        quantity: int = 1,
        success_url: str = None,
        cancel_url: str = None
    ) -> str:
        """Create Stripe Checkout session."""
        session = stripe.checkout.Session.create(
            customer=customer_id,
            mode="subscription",
            line_items=[{
                "price": price_id,
                "quantity": quantity
            }],
            success_url=success_url or f"{settings.FRONTEND_URL}/billing/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=cancel_url or f"{settings.FRONTEND_URL}/billing/cancel",
            allow_promotion_codes=True,
            billing_address_collection="required",
            metadata={
                "customer_id": customer_id
            }
        )
        
        return session.url
    
    async def create_subscription(
        self,
        customer_id: str,
        price_id: str,
        quantity: int = 1,
        trial_days: int = 0
    ) -> Dict:
        """Create subscription directly (without Checkout)."""
        params = {
            "customer": customer_id,
            "items": [{"price": price_id, "quantity": quantity}],
            "expand": ["latest_invoice.payment_intent"]
        }
        
        if trial_days > 0:
            params["trial_period_days"] = trial_days
        
        subscription = stripe.Subscription.create(**params)
        
        return {
            "subscription_id": subscription.id,
            "status": subscription.status,
            "client_secret": subscription.latest_invoice.payment_intent.client_secret if subscription.latest_invoice else None
        }
    
    async def update_subscription(
        self,
        subscription_id: str,
        price_id: Optional[str] = None,
        quantity: Optional[int] = None,
        proration_behavior: str = "create_prorations"
    ):
        """Update subscription (change plan or quantity)."""
        params = {"proration_behavior": proration_behavior}
        
        if price_id or quantity:
            subscription = stripe.Subscription.retrieve(subscription_id)
            item_id = subscription["items"]["data"][0].id
            
            params["items"] = [{
                "id": item_id,
                **({"price": price_id} if price_id else {}),
                **({"quantity": quantity} if quantity else {})
            }]
        
        return stripe.Subscription.modify(subscription_id, **params)
    
    async def cancel_subscription(
        self,
        subscription_id: str,
        at_period_end: bool = True
    ):
        """Cancel subscription."""
        if at_period_end:
            return stripe.Subscription.modify(
                subscription_id,
                cancel_at_period_end=True
            )
        else:
            return stripe.Subscription.delete(subscription_id)
    
    async def create_billing_portal_session(
        self,
        customer_id: str,
        return_url: str = None
    ) -> str:
        """Create Stripe Customer Portal session."""
        session = stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=return_url or f"{settings.FRONTEND_URL}/billing"
        )
        
        return session.url
```

## Checkout Flow

### API Endpoint

```python
# app/api/endpoints/billing.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services.stripe_service import StripeService
from app.core.auth import get_current_user

router = APIRouter(prefix="/billing", tags=["billing"])

@router.post("/checkout")
async def create_checkout(
    plan: str,
    seats: int = 1,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create Stripe Checkout session."""
    stripe_service = StripeService(db)
    
    # Get or create Stripe customer
    customer = await get_stripe_customer(db, current_user.organization_id)
    
    if not customer:
        customer_id = await stripe_service.create_customer(
            organization_id=current_user.organization_id,
            email=current_user.email
        )
    else:
        customer_id = customer.stripe_customer_id
    
    # Get price ID for plan
    price_id = get_price_id(plan)
    
    # Create checkout session
    checkout_url = await stripe_service.create_checkout_session(
        customer_id=customer_id,
        price_id=price_id,
        quantity=seats
    )
    
    return {"checkout_url": checkout_url}

@router.get("/portal")
async def get_billing_portal(
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get Stripe Customer Portal URL."""
    stripe_service = StripeService(db)
    
    customer = await get_stripe_customer(db, current_user.organization_id)
    
    if not customer:
        raise HTTPException(status_code=404, detail="No billing account found")
    
    portal_url = await stripe_service.create_billing_portal_session(
        customer_id=customer.stripe_customer_id
    )
    
    return {"portal_url": portal_url}

def get_price_id(plan: str) -> str:
    """Get Stripe price ID for plan."""
    prices = {
        "student": settings.STRIPE_PRICE_STUDENT,
        "teacher": settings.STRIPE_PRICE_TEACHER,
        "school_starter": settings.STRIPE_PRICE_SCHOOL_STARTER,
        "school_pro": settings.STRIPE_PRICE_SCHOOL_PRO
    }
    
    if plan not in prices:
        raise HTTPException(status_code=400, detail=f"Invalid plan: {plan}")
    
    return prices[plan]
```

## Webhook Processing

### Webhook Handler

```python
# app/api/endpoints/webhooks.py
from fastapi import APIRouter, Request, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
import stripe
from app.core.config import settings
from app.core.database import get_db

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

@router.post("/stripe")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None),
    db: AsyncSession = Depends(get_db)
):
    """Handle Stripe webhooks."""
    payload = await request.body()
    
    try:
        event = stripe.Webhook.construct_event(
            payload,
            stripe_signature,
            settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")
    
    # Handle event
    handler = WebhookHandler(db)
    await handler.handle_event(event)
    
    return {"status": "success"}

class WebhookHandler:
    """Process Stripe webhook events."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def handle_event(self, event: stripe.Event):
        """Route event to appropriate handler."""
        handlers = {
            "checkout.session.completed": self.handle_checkout_completed,
            "customer.subscription.created": self.handle_subscription_created,
            "customer.subscription.updated": self.handle_subscription_updated,
            "customer.subscription.deleted": self.handle_subscription_deleted,
            "invoice.payment_succeeded": self.handle_payment_succeeded,
            "invoice.payment_failed": self.handle_payment_failed
        }
        
        handler = handlers.get(event.type)
        
        if handler:
            await handler(event.data.object)
        else:
            print(f"Unhandled event type: {event.type}")
    
    async def handle_checkout_completed(self, session):
        """Handle successful checkout."""
        subscription_id = session.subscription
        customer_id = session.customer
        
        # Subscription will be handled by subscription.created event
        print(f"Checkout completed: {subscription_id}")
    
    async def handle_subscription_created(self, subscription):
        """Handle new subscription."""
        from sqlalchemy import text
        
        query = text("""
            INSERT INTO subscriptions 
                (organization_id, stripe_subscription_id, stripe_customer_id, 
                 plan_type, status, current_period_start, current_period_end)
            VALUES 
                ((SELECT organization_id FROM stripe_customers WHERE stripe_customer_id = :customer_id),
                 :subscription_id, :customer_id, :plan_type, :status,
                 to_timestamp(:period_start), to_timestamp(:period_end))
        """)
        
        await self.db.execute(query, {
            "customer_id": subscription.customer,
            "subscription_id": subscription.id,
            "plan_type": subscription.metadata.get("plan_type", "unknown"),
            "status": subscription.status,
            "period_start": subscription.current_period_start,
            "period_end": subscription.current_period_end
        })
        
        # Create license for school plans
        if "school" in subscription.metadata.get("plan_type", ""):
            quantity = subscription["items"]["data"][0].quantity
            await self.create_license(subscription.id, quantity)
        
        await self.db.commit()
    
    async def handle_subscription_updated(self, subscription):
        """Handle subscription changes."""
        from sqlalchemy import text
        
        query = text("""
            UPDATE subscriptions 
            SET status = :status,
                current_period_start = to_timestamp(:period_start),
                current_period_end = to_timestamp(:period_end),
                cancel_at_period_end = :cancel_at_period_end,
                updated_at = CURRENT_TIMESTAMP
            WHERE stripe_subscription_id = :subscription_id
        """)
        
        await self.db.execute(query, {
            "subscription_id": subscription.id,
            "status": subscription.status,
            "period_start": subscription.current_period_start,
            "period_end": subscription.current_period_end,
            "cancel_at_period_end": subscription.cancel_at_period_end
        })
        
        # Update license seats if quantity changed
        new_quantity = subscription["items"]["data"][0].quantity
        await self.update_license_seats(subscription.id, new_quantity)
        
        await self.db.commit()
    
    async def handle_subscription_deleted(self, subscription):
        """Handle subscription cancellation."""
        from sqlalchemy import text
        
        query = text("""
            UPDATE subscriptions 
            SET status = 'canceled', updated_at = CURRENT_TIMESTAMP
            WHERE stripe_subscription_id = :subscription_id
        """)
        
        await self.db.execute(query, {"subscription_id": subscription.id})
        await self.db.commit()
    
    async def handle_payment_succeeded(self, invoice):
        """Handle successful payment."""
        print(f"Payment succeeded: {invoice.id}")
        # Send receipt email, update billing history, etc.
    
    async def handle_payment_failed(self, invoice):
        """Handle failed payment."""
        print(f"Payment failed: {invoice.id}")
        # Send notification, retry payment, etc.
    
    async def create_license(self, subscription_id: str, total_seats: int):
        """Create school license."""
        from sqlalchemy import text
        
        query = text("""
            INSERT INTO school_licenses (subscription_id, organization_id, total_seats)
            VALUES (
                (SELECT subscription_id FROM subscriptions WHERE stripe_subscription_id = :subscription_id),
                (SELECT organization_id FROM subscriptions WHERE stripe_subscription_id = :subscription_id),
                :total_seats
            )
        """)
        
        await self.db.execute(query, {
            "subscription_id": subscription_id,
            "total_seats": total_seats
        })
    
    async def update_license_seats(self, subscription_id: str, new_total: int):
        """Update license seat count."""
        from sqlalchemy import text
        
        query = text("""
            UPDATE school_licenses 
            SET total_seats = :new_total,
                updated_at = CURRENT_TIMESTAMP
            WHERE subscription_id = (
                SELECT subscription_id FROM subscriptions WHERE stripe_subscription_id = :subscription_id
            )
        """)
        
        await self.db.execute(query, {
            "subscription_id": subscription_id,
            "new_total": new_total
        })
```

## License Management

### Seat Assignment Service

```python
# app/services/license_service.py
from typing import List
from uuid import UUID
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

class LicenseService:
    """Manage school license seat assignments."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def assign_seat(self, license_id: UUID, user_id: UUID) -> bool:
        """Assign seat to user."""
        # Check if seats available
        query = text("""
            SELECT seats_available 
            FROM school_licenses 
            WHERE license_id = :license_id
        """)
        
        result = await self.db.execute(query, {"license_id": str(license_id)})
        row = result.fetchone()
        
        if not row or row.seats_available <= 0:
            return False
        
        # Assign seat
        query = text("""
            INSERT INTO license_seat_assignments (license_id, user_id)
            VALUES (:license_id, :user_id)
            ON CONFLICT (license_id, user_id) DO NOTHING
        """)
        
        await self.db.execute(query, {
            "license_id": str(license_id),
            "user_id": str(user_id)
        })
        
        # Update seats_assigned count
        query = text("""
            UPDATE school_licenses 
            SET seats_assigned = (
                SELECT COUNT(*) FROM license_seat_assignments 
                WHERE license_id = :license_id AND revoked_at IS NULL
            )
            WHERE license_id = :license_id
        """)
        
        await self.db.execute(query, {"license_id": str(license_id)})
        await self.db.commit()
        
        return True
    
    async def revoke_seat(self, license_id: UUID, user_id: UUID):
        """Revoke seat from user."""
        query = text("""
            UPDATE license_seat_assignments 
            SET revoked_at = CURRENT_TIMESTAMP
            WHERE license_id = :license_id AND user_id = :user_id AND revoked_at IS NULL
        """)
        
        await self.db.execute(query, {
            "license_id": str(license_id),
            "user_id": str(user_id)
        })
        
        # Update seats_assigned count
        query = text("""
            UPDATE school_licenses 
            SET seats_assigned = (
                SELECT COUNT(*) FROM license_seat_assignments 
                WHERE license_id = :license_id AND revoked_at IS NULL
            )
            WHERE license_id = :license_id
        """)
        
        await self.db.execute(query, {"license_id": str(license_id)})
        await self.db.commit()
    
    async def get_available_seats(self, organization_id: UUID) -> int:
        """Get total available seats for organization."""
        query = text("""
            SELECT COALESCE(SUM(seats_available), 0) as total
            FROM school_licenses
            WHERE organization_id = :org_id
        """)
        
        result = await self.db.execute(query, {"org_id": str(organization_id)})
        row = result.fetchone()
        
        return row.total if row else 0
```

## Testing Strategy

```python
# tests/test_stripe_service.py
import pytest
from unittest.mock import patch, MagicMock
from app.services.stripe_service import StripeService

@pytest.mark.asyncio
async def test_create_checkout_session(db_session):
    """Test Stripe checkout session creation."""
    service = StripeService(db_session)
    
    with patch("stripe.checkout.Session.create") as mock_create:
        mock_create.return_value = MagicMock(url="https://checkout.stripe.com/test")
        
        url = await service.create_checkout_session(
            customer_id="cus_test123",
            price_id="price_test123"
        )
        
        assert "checkout.stripe.com" in url
        mock_create.assert_called_once()

@pytest.mark.asyncio
async def test_webhook_subscription_created(db_session):
    """Test subscription.created webhook."""
    from app.api.endpoints.webhooks import WebhookHandler
    
    handler = WebhookHandler(db_session)
    
    # Mock Stripe subscription object
    subscription = MagicMock(
        id="sub_test123",
        customer="cus_test123",
        status="active",
        current_period_start=1234567890,
        current_period_end=1234567890,
        metadata={"plan_type": "teacher"}
    )
    
    await handler.handle_subscription_created(subscription)
    
    # Verify subscription saved to database
    # ...
```

## Summary

Stripe integration provides:

1. **Subscription management**: Monthly/annual individual and school licenses
2. **Secure checkout**: Stripe Checkout with PCI compliance
3. **Webhook processing**: Real-time subscription updates
4. **License management**: Seat assignments with availability tracking
5. **Customer portal**: Self-service billing management

**Key Features**:
- Automatic proration for plan changes
- Trial periods support
- Promotion codes
- Failed payment retries
- Subscription analytics

**Next Steps**:
- Implement usage-based billing for API calls
- Add multi-currency support
- Build admin dashboard for subscription analytics
- Implement seat reclamation for inactive users
