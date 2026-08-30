"""
Payment endpoints with Razorpay integration.
Implements payment state machine and duplicate prevention.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.database import get_db
from models.models import Payment, Order, Approval
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import os
import uuid
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID", "")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "")

# Valid order status transitions
VALID_TRANSITIONS = {
    "created": ["approval_pending", "cancelled"],
    "approval_pending": ["approved", "cancelled"],
    "approved": ["payment_initiated"],
    "payment_initiated": ["success", "failed"],
    "success": [],  # Terminal state
    "failed": [],   # Terminal state - must create new order to retry
    "cancelled": [],  # Terminal state
}


class PaymentCreate(BaseModel):
    order_id: str


class PaymentResponse(BaseModel):
    id: str
    order_id: str
    amount: float
    currency: str
    status: str
    razorpay_order_id: Optional[str]
    razorpay_payment_id: Optional[str]
    failure_reason: Optional[str]
    created_at: Optional[datetime] = None


def get_razorpay_client():
    if not RAZORPAY_KEY_ID or not RAZORPAY_KEY_SECRET or "placeholder" in RAZORPAY_KEY_ID.lower():
        logger.info("Razorpay not configured, using demo mode")
        return None
    """Get Razorpay client. Import lazily to avoid crash if not installed."""
    try:
        import razorpay
        return razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))
    except ImportError:
        logger.warning("razorpay package not installed")
        return None


@router.get("/", response_model=List[PaymentResponse])
async def list_payments(limit: int = 50, db: AsyncSession = Depends(get_db)):
    """List all payments (most recent first)."""
    result = await db.execute(
        select(Payment).order_by(Payment.created_at.desc()).limit(limit)
    )
    payments = result.scalars().all()
    return [
        PaymentResponse(
            id=p.id,
            order_id=p.order_id,
            amount=p.amount,
            currency=p.currency,
            status=p.status,
            razorpay_order_id=p.razorpay_order_id,
            razorpay_payment_id=p.razorpay_payment_id,
            failure_reason=p.failure_reason,
            created_at=p.created_at
        ) for p in payments
    ]


@router.post("/", response_model=PaymentResponse)
async def create_payment(payment: PaymentCreate, db: AsyncSession = Depends(get_db)):
    """Create a payment for an approved order."""
    # 1. Verify order exists
    order_result = await db.execute(select(Order).where(Order.id == payment.order_id))
    order = order_result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # 2. Verify order is approved
    if order.status != "approved":
        raise HTTPException(status_code=400, detail=f"Order is not approved. Current status: {order.status}")

    # 3. Check for existing successful payment
    existing_success = await db.execute(
        select(Payment).where(Payment.order_id == payment.order_id, Payment.status == "success")
    )
    if existing_success.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Payment already completed for this order")

    # 4. Check for payment already in progress
    existing_initiated = await db.execute(
        select(Payment).where(
            Payment.order_id == payment.order_id,
            Payment.status.in_(["initiated", "created"])
        )
    )
    if existing_initiated.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Payment already in progress for this order")

    # 5. Verify approval exists and is valid
    approval_result = await db.execute(
        select(Approval).where(
            Approval.order_id == order.id,
            Approval.status == "approved"
        )
    )
    approval = approval_result.scalar_one_or_none()
    if not approval:
        raise HTTPException(status_code=403, detail="No valid approval found for this order")

    # 6. Create Razorpay order
    try:
        client = get_razorpay_client()
        if client:
            razorpay_order = client.order.create({
                "amount": int(order.total * 100),  # Razorpay expects paise
                "currency": "INR",
                "receipt": str(order.id),
            })
            razorpay_order_id = razorpay_order["id"]
            status = "initiated"
        else:
            # Demo mode - simulate Razorpay order creation
            razorpay_order_id = f"order_demo_{uuid.uuid4().hex[:8]}"
            status = "initiated"
            logger.warning("Razorpay not configured, using demo order ID")
    except Exception as e:
        logger.error(f"Razorpay order creation failed: {e}")
        razorpay_order_id = f"fail_{uuid.uuid4().hex[:8]}"
        status = "failed"

    # 7. Create payment record
    payment_record = Payment(
        order_id=payment.order_id,
        amount=order.total,
        currency="INR",
        status=status,
        razorpay_order_id=razorpay_order_id
    )
    db.add(payment_record)

    # 8. Update order status (state machine: approved -> payment_initiated)
    order.status = "payment_initiated"
    order.razorpay_order_id = razorpay_order_id

    await db.commit()
    await db.refresh(payment_record)

    return PaymentResponse(
        id=payment_record.id,
        order_id=payment_record.order_id,
        amount=payment_record.amount,
        currency=payment_record.currency,
        status=payment_record.status,
        razorpay_order_id=payment_record.razorpay_order_id,
        razorpay_payment_id=payment_record.razorpay_payment_id,
        failure_reason=payment_record.failure_reason,
        created_at=payment_record.created_at
    )


@router.get("/{payment_id}", response_model=PaymentResponse)
async def get_payment(payment_id: str, db: AsyncSession = Depends(get_db)):
    """Get a specific payment."""
    result = await db.execute(select(Payment).where(Payment.id == payment_id))
    payment = result.scalar_one_or_none()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return PaymentResponse(
        id=payment.id,
        order_id=payment.order_id,
        amount=payment.amount,
        currency=payment.currency,
        status=payment.status,
        razorpay_order_id=payment.razorpay_order_id,
        razorpay_payment_id=payment.razorpay_payment_id,
        failure_reason=payment.failure_reason,
        created_at=payment.created_at
    )


@router.post("/demo-fail/{payment_id}", response_model=PaymentResponse)
async def demo_fail_payment(payment_id: str, db: AsyncSession = Depends(get_db)):
    """Simulate a payment failure for demo purposes."""
    result = await db.execute(select(Payment).where(Payment.id == payment_id))
    payment = result.scalar_one_or_none()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    # Only allow failing initiated payments
    if payment.status not in ("initiated", "created"):
        raise HTTPException(status_code=400, detail=f"Cannot fail payment in status: {payment.status}")

    payment.status = "failed"
    payment.failure_reason = "[DEMO] Simulated failure: Insufficient funds (this is a test, not a real failure)"

    # Update order status
    order_result = await db.execute(select(Order).where(Order.id == payment.order_id))
    order = order_result.scalar_one_or_none()
    if order:
        order.status = "failed"

    await db.commit()
    await db.refresh(payment)

    return PaymentResponse(
        id=payment.id,
        order_id=payment.order_id,
        amount=payment.amount,
        currency=payment.currency,
        status=payment.status,
        razorpay_order_id=payment.razorpay_order_id,
        razorpay_payment_id=payment.razorpay_payment_id,
        failure_reason=payment.failure_reason,
        created_at=payment.created_at
    )
