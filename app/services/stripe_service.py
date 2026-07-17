"""
Stripe billing service: customer/checkout/portal sessions and idempotent
webhook event application onto the subscriptions table
"""
import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional

import stripe
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.subscription import Subscription
from app.models.user import User

logger = logging.getLogger(__name__)


def _stripe_ready() -> None:
    if not settings.STRIPE_SECRET_KEY:
        raise HTTPException(
            status_code=503,
            detail={"code": "billing_not_configured", "message": "Billing is not configured."},
        )
    stripe.api_key = settings.STRIPE_SECRET_KEY


def _sanitize_return_to(return_to: Optional[str]) -> str:
    # In-app path only — anything else would be an open redirect
    if return_to and return_to.startswith("/") and not return_to.startswith("//"):
        return return_to
    return "/dashboard"


async def _get_by_user(db: AsyncSession, user_id) -> Optional[Subscription]:
    result = await db.execute(select(Subscription).where(Subscription.user_id == user_id))
    return result.scalar_one_or_none()


async def _get_by_customer(db: AsyncSession, customer_id) -> Optional[Subscription]:
    if not customer_id:
        return None
    result = await db.execute(
        select(Subscription).where(Subscription.stripe_customer_id == customer_id)
    )
    return result.scalar_one_or_none()


async def get_or_create_customer(db: AsyncSession, user: User) -> Subscription:
    row = await _get_by_user(db, user.id)
    if row:
        return row
    _stripe_ready()
    customer = await asyncio.to_thread(
        stripe.Customer.create, email=user.email, metadata={"user_id": str(user.id)}
    )
    row = Subscription(user_id=user.id, stripe_customer_id=customer["id"])
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


async def create_checkout_session(
    db: AsyncSession, user: User, return_to: Optional[str] = None
) -> str:
    _stripe_ready()
    if not settings.STRIPE_PRICE_ID:
        raise HTTPException(
            status_code=503,
            detail={"code": "billing_not_configured", "message": "Billing is not configured."},
        )
    row = await get_or_create_customer(db, user)
    path = _sanitize_return_to(return_to)
    session = await asyncio.to_thread(
        stripe.checkout.Session.create,
        mode="subscription",
        customer=row.stripe_customer_id,
        client_reference_id=str(user.id),
        line_items=[{"price": settings.STRIPE_PRICE_ID, "quantity": 1}],
        success_url=(
            f"{settings.FRONTEND_URL}/#/billing/success"
            f"?session_id={{CHECKOUT_SESSION_ID}}&return_to={path}"
        ),
        cancel_url=f"{settings.FRONTEND_URL}/#/billing/canceled",
    )
    return session["url"]


async def create_portal_session(db: AsyncSession, user: User) -> str:
    row = await _get_by_user(db, user.id)
    if row is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "no_subscription", "message": "No subscription on file."},
        )
    _stripe_ready()
    session = await asyncio.to_thread(
        stripe.billing_portal.Session.create,
        customer=row.stripe_customer_id,
        return_url=f"{settings.FRONTEND_URL}/#/dashboard",
    )
    return session["url"]


def _period_end(sub_obj: dict) -> Optional[datetime]:
    ts = sub_obj.get("current_period_end")
    if ts is None:
        # Stripe API >= 2025-03-31 keeps the period on the subscription item
        items = (sub_obj.get("items") or {}).get("data") or []
        if items:
            ts = items[0].get("current_period_end")
    return datetime.fromtimestamp(ts, tz=timezone.utc) if ts else None


def _apply_snapshot(row: Subscription, sub_obj: dict) -> None:
    if sub_obj.get("id"):
        row.stripe_subscription_id = sub_obj["id"]
    if sub_obj.get("status"):
        row.status = sub_obj["status"]
    row.cancel_at_period_end = bool(sub_obj.get("cancel_at_period_end", False))
    period_end = _period_end(sub_obj)
    if period_end:
        row.current_period_end = period_end
    items = (sub_obj.get("items") or {}).get("data") or []
    price_id = (items[0].get("price") or {}).get("id") if items else None
    if price_id:
        row.price_id = price_id


def _is_stale(row: Subscription, event_created: int) -> bool:
    return row.last_event_created is not None and event_created < row.last_event_created


async def sync_from_checkout_session(db: AsyncSession, user: User, session_id: str) -> Subscription:
    """Server-side sync right after the Checkout redirect, before the webhook lands."""
    _stripe_ready()
    session = await asyncio.to_thread(stripe.checkout.Session.retrieve, session_id)
    if session.get("client_reference_id") != str(user.id):
        raise HTTPException(
            status_code=403,
            detail={"code": "session_ownership_mismatch", "message": "Not your checkout session."},
        )
    row = await _get_by_user(db, user.id)
    if row is None:
        row = Subscription(user_id=user.id, stripe_customer_id=session.get("customer") or "")
        db.add(row)
    subscription_id = session.get("subscription")
    if subscription_id:
        sub_obj = await asyncio.to_thread(stripe.Subscription.retrieve, subscription_id)
        _apply_snapshot(row, sub_obj)
    await db.commit()
    await db.refresh(row)
    return row


async def apply_stripe_event(db: AsyncSession, event: dict) -> None:
    """Apply one webhook event. Absolute snapshots + last_event_created guard
    make replays harmless and out-of-order deliveries inert."""
    event_type = event.get("type", "")
    event_created = event.get("created") or 0
    obj = (event.get("data") or {}).get("object") or {}

    if event_type == "checkout.session.completed":
        row = await _get_by_customer(db, obj.get("customer"))
        if row is None:
            logger.warning("Stripe checkout completed for unknown customer %s", obj.get("customer"))
            return
        if _is_stale(row, event_created):
            return
        subscription_id = obj.get("subscription")
        if subscription_id:
            row.stripe_subscription_id = subscription_id
            _stripe_ready()
            # Live retrieve is always-current, immune to event ordering
            sub_obj = await asyncio.to_thread(stripe.Subscription.retrieve, subscription_id)
            _apply_snapshot(row, sub_obj)
        row.last_event_created = event_created
        await db.commit()
    elif event_type in (
        "customer.subscription.created",
        "customer.subscription.updated",
        "customer.subscription.deleted",
    ):
        row = await _get_by_customer(db, obj.get("customer"))
        if row is None:
            logger.warning("Stripe %s for unknown customer %s", event_type, obj.get("customer"))
            return
        if _is_stale(row, event_created):
            return
        _apply_snapshot(row, obj)
        row.last_event_created = event_created
        await db.commit()
    elif event_type == "invoice.payment_failed":
        if not obj.get("subscription"):
            return
        row = await _get_by_customer(db, obj.get("customer"))
        if row is None:
            logger.warning("Stripe payment_failed for unknown customer %s", obj.get("customer"))
            return
        if _is_stale(row, event_created):
            return
        row.status = "past_due"
        row.last_event_created = event_created
        await db.commit()
        logger.info("Subscription for customer %s marked past_due", obj.get("customer"))
    else:
        logger.info("Ignoring stripe event type %s", event_type)
