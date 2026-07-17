"""
Billing endpoints: Stripe checkout, customer portal, subscription status
"""
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db, get_current_user
from app.core.entitlements import is_entitled
from app.models.subscription import Subscription
from app.models.user import User
from app.services import stripe_service

router = APIRouter()


class CheckoutRequest(BaseModel):
    return_to: Optional[str] = None


class VerifySessionRequest(BaseModel):
    session_id: str


def _status_payload(subscription: Optional[Subscription]) -> dict:
    return {
        "status": subscription.status if subscription else None,
        "is_entitled": is_entitled(subscription),
        "current_period_end": (
            subscription.current_period_end.isoformat()
            if subscription and subscription.current_period_end
            else None
        ),
        "cancel_at_period_end": bool(subscription.cancel_at_period_end) if subscription else False,
    }


@router.post("/checkout-session")
async def checkout_session(
    request: CheckoutRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    url = await stripe_service.create_checkout_session(db, current_user, request.return_to)
    return {"url": url}


@router.post("/portal-session")
async def portal_session(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    url = await stripe_service.create_portal_session(db, current_user)
    return {"url": url}


@router.get("/status")
async def billing_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    subscription = await stripe_service.get_subscription_for_user(db, current_user.id)
    return _status_payload(subscription)


@router.post("/verify-session")
async def verify_session(
    request: VerifySessionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    subscription = await stripe_service.sync_from_checkout_session(
        db, current_user, request.session_id
    )
    return _status_payload(subscription)
