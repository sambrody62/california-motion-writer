"""
Stripe webhook endpoint — unauthenticated, verified by signature
"""
import json
import logging

import stripe
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.services.stripe_service import apply_stripe_event

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/stripe")
async def stripe_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    payload = await request.body()
    signature = request.headers.get("stripe-signature")
    if not signature:
        raise HTTPException(status_code=400, detail="Missing stripe-signature header")
    try:
        stripe.Webhook.construct_event(payload, signature, settings.STRIPE_WEBHOOK_SECRET)
    except (ValueError, stripe.SignatureVerificationError):
        logger.warning("Rejected stripe webhook with invalid signature")
        raise HTTPException(status_code=400, detail="Invalid webhook signature")
    # apply_stripe_event works on plain dicts; the payload is signature-verified
    await apply_stripe_event(db, json.loads(payload))
    return {"received": True}
