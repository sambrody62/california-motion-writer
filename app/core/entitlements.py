"""
Subscription entitlement gate for paid features (LLM drafting, PDF export)
"""
import os

from fastapi import Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.subscription import Subscription
from app.models.user import User

# past_due stays entitled: a failed renewal charge must not lock a user out
# mid-motion. Revocation is delegated to Stripe dunning — when retries
# exhaust, Stripe cancels the subscription and the webhook lands "canceled".
ENTITLED_STATUSES = {"active", "trialing", "past_due"}


def is_entitled(subscription: Subscription | None) -> bool:
    return subscription is not None and subscription.status in ENTITLED_STATUSES


async def require_active_subscription(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    # Read at request time (mirrors RATE_LIMIT_ENABLED) so tests and ops can
    # flip the flag without a reimport
    if os.getenv("BILLING_ENABLED", "true").lower() != "true":
        return
    result = await db.execute(
        select(Subscription).where(Subscription.user_id == current_user.id)
    )
    if is_entitled(result.scalar_one_or_none()):
        return
    raise HTTPException(
        status_code=402,
        detail={
            "code": "subscription_required",
            "message": "An active subscription is required to draft and export motions.",
        },
    )
