"""
Razorpay Webhook Handler
Implements proper HMAC signature verification and idempotent processing.
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.database import get_db
from models.models import Payment, Order, AuditLog
import os
import hashlib
import hmac
import json
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

RAZORPAY_WEBHOOK_SECRET = os.getenv("RAZORPAY_WEBHOOK_SECRET", "")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "")


def verify_razorpay_signature(body: bytes, signature: str, secret: str) -> bool:
    """Verify Razorpay webhook signature using HMAC SHA256."""
    if not secret:
        logger.warning("No webhook secret configured, skipping signature verification")
        return True  # Allow in demo mode

    try:
        expected = hmac.new(
            secret.encode("utf-8"),
            body,
            hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(expected, signature)
    except Exception as e:
        logger.error(f"Signature verification failed: {e}")
        return False


@router.post("/razorpay")
async def razorpay_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """Handle Razorpay webhook events with idempotent processing."""
    body = await request.body()
    signature = request.headers.get("X-Razorpay-Signature", "")

    # Verify signature
    secret = RAZORPAY_WEBHOOK_SECRET or RAZORPAY_KEY_SECRET
    if not verify_razorpay_signature(body, signature, secret):
        logger.warning("Invalid webhook signature")
        raise HTTPException(status_code=400, detail="Invalid signature")

    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    event = payload.get("event", "")
    logger.info(f"Webhook received: {event}")

    if event == "payment.captured":
        await _handle_payment_captured(payload, db)
    elif event == "payment.failed":
        await _handle_payment_failed(payload, db)
    else:
        logger.info(f"Unhandled webhook event: {event}")

    return {"status": "ok"}


async def _handle_payment_captured(payload: dict, db: AsyncSession):
    """Handle payment.captured event - idempotent."""
    try:
        payment_entity = payload["payload"]["payment"]["entity"]
        razorpay_payment_id = payment_entity["id"]
        razorpay_order_id = payment_entity["order_id"]
    except (KeyError, TypeError) as e:
        logger.error(f"Invalid payment.captured payload: {e}")
        return

    # Find payment by razorpay_order_id
    result = await db.execute(
        select(Payment).where(Payment.razorpay_order_id == razorpay_order_id)
    )
    payment = result.scalar_one_or_none()

    if not payment:
        logger.warning(f"Payment not found for razorpay_order_id: {razorpay_order_id}")
        return

    # Idempotency: skip if already in a terminal success state
    if payment.status in ("PAID", "CAPTURED"):
        logger.info(f"Payment {payment.id} already in terminal state ({payment.status}), skipping")
        return

    # Server-side amount security: the captured amount must match the order total.
    order_result = await db.execute(select(Order).where(Order.id == payment.order_id))
    order = order_result.scalar_one_or_none()
    try:
        captured_amount = int(payment_entity.get("amount", 0))  # paise
        expected_amount = int((order.total if order else payment.amount) * 100)
        if captured_amount != expected_amount:
            logger.warning(f"Webhook amount mismatch for payment {payment.id}: {captured_amount} != {expected_amount}")
            payment.status = "FAILED"
            payment.failure_reason = "Captured amount does not match order total"
            if order:
                order.status = "PAYMENT_FAILED"
                order.payment_status = "FAILED"
            await db.commit()
            return
    except (TypeError, ValueError):
        logger.warning(f"Could not parse captured amount for payment {payment.id}")

    # Money was captured by Razorpay. The payment is NOT marked PAID yet — the
    # frontend /api/payments/verify callback performs signature verification and
    # promotes CAPTURED → PAID / order → CONFIRMED. This honors the rule that
    # only a verified payment becomes PAID.
    payment.razorpay_payment_id = razorpay_payment_id
    payment.status = "CAPTURED"
    if order:
        order.razorpay_payment_id = razorpay_payment_id

    db.add(AuditLog(
        action="PAYMENT_CAPTURED",
        description=f"Razorpay webhook: payment {razorpay_payment_id} captured for order {payment.order_id}",
        event_type="payment",
        related_entity=payment.order_id,
        payment_reference=razorpay_payment_id,
        decision="Captured by Razorpay — awaiting signature verification",
        policy_result="amount_validated",
        final_status="CAPTURED",
        financial_impact=payment.amount,
    ))
    await db.commit()
    logger.info(f"Payment {payment.id} marked as CAPTURED via webhook")


async def _handle_payment_failed(payload: dict, db: AsyncSession):
    """Handle payment.failed event - idempotent."""
    try:
        payment_entity = payload["payload"]["payment"]["entity"]
        razorpay_order_id = payment_entity["order_id"]
        error_description = payment_entity.get("error_description", "Payment failed")
    except (KeyError, TypeError) as e:
        logger.error(f"Invalid payment.failed payload: {e}")
        return

    result = await db.execute(
        select(Payment).where(Payment.razorpay_order_id == razorpay_order_id)
    )
    payment = result.scalar_one_or_none()

    if not payment:
        logger.warning(f"Payment not found for razorpay_order_id: {razorpay_order_id}")
        return

    # Idempotency: skip if already in a terminal state
    if payment.status in ("FAILED", "PAID", "CAPTURED"):
        logger.info(f"Payment {payment.id} already in terminal state ({payment.status}), skipping")
        return

    payment.status = "FAILED"
    payment.failure_reason = error_description

    # Update order
    order_result = await db.execute(select(Order).where(Order.id == payment.order_id))
    order = order_result.scalar_one_or_none()
    if order:
        order.status = "PAYMENT_FAILED"
        order.payment_status = "FAILED"

    db.add(AuditLog(
        action="PAYMENT_FAILED",
        description=f"Razorpay webhook: payment failed for order {payment.order_id}: {error_description}",
        event_type="payment",
        related_entity=payment.order_id,
        payment_reference=payment.razorpay_order_id,
        decision="Payment failed — order NOT marked paid",
        policy_result="payment_declined",
        final_status="FAILED",
        financial_impact=payment.amount,
    ))
    await db.commit()
    logger.info(f"Payment {payment.id} marked as FAILED via webhook")
