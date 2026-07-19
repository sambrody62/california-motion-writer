"""
Stripe service: customer creation, checkout URL building, and idempotent
webhook event application
"""
from datetime import datetime, timezone
from unittest.mock import patch

import pytest
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.subscription import Subscription
from app.models.user import User
from app.services.stripe_service import (
    apply_stripe_event,
    create_checkout_session,
    get_or_create_customer,
)

pytestmark = pytest.mark.asyncio

PERIOD_END = 1893456000  # 2030-01-01


@pytest.fixture
def stripe_key(monkeypatch):
    monkeypatch.setattr(settings, "STRIPE_SECRET_KEY", "sk_test_key")
    monkeypatch.setattr(settings, "STRIPE_PRICE_ID", "price_test")
    monkeypatch.setattr(settings, "STRIPE_SETUP_PRICE_ID", "price_setup")


def _sub_object(status="active", customer="cus_1", sub_id="sub_1", cancel=False):
    return {
        "id": sub_id,
        "customer": customer,
        "status": status,
        "current_period_end": PERIOD_END,
        "cancel_at_period_end": cancel,
        "items": {"data": [{"price": {"id": "price_test"}}]},
    }


def _sub_event(etype="customer.subscription.updated", created=100, **kwargs):
    return {"type": etype, "created": created, "data": {"object": _sub_object(**kwargs)}}


async def _make_row(test_db, test_user, **kwargs) -> Subscription:
    row = Subscription(
        user_id=test_user.id, stripe_customer_id=kwargs.pop("stripe_customer_id", "cus_1"), **kwargs
    )
    test_db.add(row)
    await test_db.commit()
    await test_db.refresh(row)
    return row


async def test_get_or_create_customer_creates_once(
    test_db: AsyncSession, test_user: User, stripe_key
):
    with patch("app.services.stripe_service.stripe.Customer.create") as create:
        create.return_value = {"id": "cus_new"}
        first = await get_or_create_customer(test_db, test_user)
        second = await get_or_create_customer(test_db, test_user)

    assert create.call_count == 1
    assert first.stripe_customer_id == "cus_new"
    assert first.status == "incomplete"
    assert second.id == first.id


async def test_create_checkout_session_builds_urls(
    test_db: AsyncSession, test_user: User, stripe_key
):
    await _make_row(test_db, test_user)
    with patch("app.services.stripe_service.stripe.checkout.Session.create") as create:
        create.return_value = {"url": "https://checkout.stripe.com/c/pay/x"}
        url = await create_checkout_session(test_db, test_user, "/motion/1/preview")

    assert url == "https://checkout.stripe.com/c/pay/x"
    kwargs = create.call_args.kwargs
    assert kwargs["mode"] == "subscription"
    assert kwargs["customer"] == "cus_1"
    assert kwargs["client_reference_id"] == str(test_user.id)
    # One-time $499 setup fee joins the first invoice; $99/mo price defines the subscription
    assert kwargs["line_items"] == [
        {"price": "price_setup", "quantity": 1},
        {"price": "price_test", "quantity": 1},
    ]
    assert "#/billing/success?session_id={CHECKOUT_SESSION_ID}" in kwargs["success_url"]
    assert "return_to=/motion/1/preview" in kwargs["success_url"]
    assert kwargs["cancel_url"].endswith("#/billing/canceled")


async def test_checkout_503_without_setup_price(
    test_db: AsyncSession, test_user: User, stripe_key, monkeypatch
):
    # Missing setup price would silently sell $99/mo without the $499 — refuse instead
    monkeypatch.setattr(settings, "STRIPE_SETUP_PRICE_ID", "")
    await _make_row(test_db, test_user)
    with pytest.raises(HTTPException) as exc_info:
        await create_checkout_session(test_db, test_user, "/dashboard")
    assert exc_info.value.status_code == 503


@pytest.mark.parametrize("bad", ["//evil.com", "https://evil.com", "javascript:x"])
async def test_checkout_return_to_sanitized(
    test_db: AsyncSession, test_user: User, stripe_key, bad
):
    await _make_row(test_db, test_user)
    with patch("app.services.stripe_service.stripe.checkout.Session.create") as create:
        create.return_value = {"url": "https://checkout.stripe.com/c/pay/x"}
        await create_checkout_session(test_db, test_user, bad)
    assert "return_to=/dashboard" in create.call_args.kwargs["success_url"]


async def test_subscription_updated_snapshots_row(test_db: AsyncSession, test_user: User):
    await _make_row(test_db, test_user)
    await apply_stripe_event(test_db, _sub_event(created=100, cancel=True))

    row = (await test_db.execute(select(Subscription))).scalar_one()
    assert row.status == "active"
    assert row.stripe_subscription_id == "sub_1"
    assert row.price_id == "price_test"
    assert row.cancel_at_period_end is True
    assert row.current_period_end == datetime.fromtimestamp(PERIOD_END, tz=timezone.utc).replace(
        tzinfo=row.current_period_end.tzinfo
    )
    assert row.last_event_created == 100


async def test_subscription_deleted_marks_canceled(test_db: AsyncSession, test_user: User):
    await _make_row(test_db, test_user, status="active")
    await apply_stripe_event(
        test_db, _sub_event("customer.subscription.deleted", created=200, status="canceled")
    )
    row = (await test_db.execute(select(Subscription))).scalar_one()
    assert row.status == "canceled"


async def test_invoice_payment_failed_sets_past_due(test_db: AsyncSession, test_user: User):
    await _make_row(test_db, test_user, status="active")
    event = {
        "type": "invoice.payment_failed",
        "created": 300,
        "data": {"object": {"customer": "cus_1", "subscription": "sub_1"}},
    }
    await apply_stripe_event(test_db, event)
    row = (await test_db.execute(select(Subscription))).scalar_one()
    assert row.status == "past_due"


async def test_checkout_completed_links_and_retrieves(
    test_db: AsyncSession, test_user: User, stripe_key
):
    await _make_row(test_db, test_user)
    event = {
        "type": "checkout.session.completed",
        "created": 400,
        "data": {
            "object": {
                "id": "cs_1",
                "customer": "cus_1",
                "subscription": "sub_9",
                "client_reference_id": str(test_user.id),
            }
        },
    }
    with patch("app.services.stripe_service.stripe.Subscription.retrieve") as retrieve:
        retrieve.return_value = _sub_object(sub_id="sub_9")
        await apply_stripe_event(test_db, event)

    row = (await test_db.execute(select(Subscription))).scalar_one()
    assert row.stripe_subscription_id == "sub_9"
    assert row.status == "active"


async def test_replay_same_event_is_noop(test_db: AsyncSession, test_user: User):
    await _make_row(test_db, test_user)
    event = _sub_event(created=500)
    await apply_stripe_event(test_db, event)
    await apply_stripe_event(test_db, event)
    row = (await test_db.execute(select(Subscription))).scalar_one()
    assert row.status == "active"
    assert row.last_event_created == 500


async def test_stale_older_event_skipped(test_db: AsyncSession, test_user: User):
    await _make_row(test_db, test_user)
    await apply_stripe_event(test_db, _sub_event(created=600, status="canceled"))
    await apply_stripe_event(test_db, _sub_event(created=550, status="active"))
    row = (await test_db.execute(select(Subscription))).scalar_one()
    assert row.status == "canceled"
    assert row.last_event_created == 600


async def test_unknown_customer_tolerated(test_db: AsyncSession, test_user: User):
    # No row exists at all — must not raise (webhook returns 200 so Stripe stops retrying)
    await apply_stripe_event(test_db, _sub_event(customer="cus_nobody"))
    assert (await test_db.execute(select(Subscription))).scalar_one_or_none() is None


async def test_period_end_item_level_fallback(test_db: AsyncSession, test_user: User):
    # Stripe API >= 2025-03-31 moved current_period_end onto the item
    await _make_row(test_db, test_user)
    obj = _sub_object()
    del obj["current_period_end"]
    obj["items"]["data"][0]["current_period_end"] = PERIOD_END
    await apply_stripe_event(
        test_db, {"type": "customer.subscription.updated", "created": 700, "data": {"object": obj}}
    )
    row = (await test_db.execute(select(Subscription))).scalar_one()
    assert row.current_period_end is not None
