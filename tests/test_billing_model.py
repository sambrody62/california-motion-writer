"""
Tests for the Subscription model
"""
import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.subscription import Subscription
from app.models.user import User


@pytest.mark.asyncio
async def test_subscription_defaults(test_db: AsyncSession, test_user: User):
    sub = Subscription(user_id=test_user.id, stripe_customer_id="cus_123")
    test_db.add(sub)
    await test_db.commit()
    await test_db.refresh(sub)

    assert sub.id is not None
    assert sub.status == "incomplete"
    assert sub.stripe_subscription_id is None
    assert sub.price_id is None
    assert sub.current_period_end is None
    assert sub.cancel_at_period_end is False
    assert sub.last_event_created is None
    assert sub.created_at is not None
    assert sub.updated_at is not None


@pytest.mark.asyncio
async def test_one_subscription_per_user(test_db: AsyncSession, test_user: User):
    test_db.add(Subscription(user_id=test_user.id, stripe_customer_id="cus_1"))
    await test_db.commit()

    test_db.add(Subscription(user_id=test_user.id, stripe_customer_id="cus_2"))
    with pytest.raises(IntegrityError):
        await test_db.commit()
    await test_db.rollback()


@pytest.mark.asyncio
async def test_stripe_subscription_id_unique(test_db: AsyncSession, test_user: User):
    other = User(
        email="other@example.com",
        password_hash="x",
        full_name="Other User",
    )
    test_db.add(other)
    await test_db.commit()
    await test_db.refresh(other)

    test_db.add(
        Subscription(
            user_id=test_user.id, stripe_customer_id="cus_1", stripe_subscription_id="sub_1"
        )
    )
    await test_db.commit()

    test_db.add(
        Subscription(
            user_id=other.id, stripe_customer_id="cus_2", stripe_subscription_id="sub_1"
        )
    )
    with pytest.raises(IntegrityError):
        await test_db.commit()
    await test_db.rollback()
