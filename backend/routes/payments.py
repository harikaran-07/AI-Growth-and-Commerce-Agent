"""
Payment endpoints with Razorpay integration.
Implements payment state machine, create-order, verify, and duplicate prevention.
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.database import get_db
from models.models import Payment, Order, Product, CartItem, AuditLog
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone
import os
import uuid
import hashlib
import hmac
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID", "")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "")


class PaymentCreate(BaseModel):
    order_id: str


class RazorpayOrderRequest(BaseModel):
    order_id: str


class RazorpayVerifyRequest(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str
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
        return None
    try:
        import razorpay
        return razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))
    except ImportError:
        logger.warning("razorpay package not installed")
        return None


def verify_razorpay_signature(order_id: str, payment_id: str, signature: str) -> bool:
    """Verify Razorpay payment signature."""
    if not RAZORPAY_KEY_SECRET:
        logger.warning("No Razorpay secret configured, skipping verification")
        return True
    try:
        payload = f"{order_id}|{payment_id}"
        expected = hmac.new(
            RAZORPAY_KEY_SECRET.encode("utf-8"),
            payload.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(expected, signature)
    except Exception as e:
        logger.error(f"Signature verification failed: {e}")
        return False


@router.get("/", response_model=List[PaymentResponse])
async def list_payments(limit: int = 50, db: AsyncSession = Depends(get_db)):
    """List all payments (most recent first)."""
    result = await db.execute(
        select(Payment).order_by(Payment.created_at.desc()).limit(limit)
    )
    payments = result.scalars().all()
    return [
        PaymentResponse(
            id=p.id, order_id=p.order_id, amount=p.amount, currency=p.currency,
            status=p.status, razorpay_order_id=p.razorpay_order_id,
            razorpay_payment_id=p.razorpay_payment_id, failure_reason=p.failure_reason,
            created_at=p.created_at
        ) for p in payments
    ]


@router.post("/create-order")
async def create_razorpay_order(request: RazorpayOrderRequest, db: AsyncSession = Depends(get_db)):
    """Create a Razorpay order for the given order_id."""
    # Verify order exists and is in the right state
    order_result = await db.execute(select(Order).where(Order.id == request.order_id))
    order = order_result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.status not in ("pending", "payment_failed"):
        raise HTTPException(status_code=400, detail=f"Order cannot be paid. Status: {order.status}")

    # Check for existing successful payment
    existing_success = await db.execute(
        select(Payment).where(Payment.order_id == order.id, Payment.status == "success")
    )
    if existing_success.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Payment already completed for this order")

    client = get_razorpay_client()
    if client:
        try:
            razorpay_order = client.order.create({
                "amount": int(order.total * 100),  # paise
                "currency": "INR",
                "receipt": str(order.id),
            })
            razorpay_order_id = razorpay_order["id"]
        except Exception as e:
            logger.error(f"Razorpay order creation failed: {e}")
            raise HTTPException(status_code=500, detail="Payment gateway error")
    else:
        # Demo mode
        razorpay_order_id = f"order_demo_{uuid.uuid4().hex[:12]}"
        logger.warning("Razorpay not configured, using demo order ID")

    # Create payment record
    payment = Payment(
        order_id=order.id,
        amount=order.total,
        currency="INR",
        status="initiated",
        razorpay_order_id=razorpay_order_id,
    )
    db.add(payment)

    # Update order
    order.status = "payment_initiated"
    order.payment_status = "processing"
    order.razorpay_order_id = razorpay_order_id

    # Audit
    audit = AuditLog(
        action="PAYMENT_INITIATED",
        description=f"Razorpay order created for order {order.id}, amount: {order.total}",
        event_type="payment",
        related_entity=order.id,
        financial_impact=order.total,
        final_status="initiated",
    )
    db.add(audit)
    await db.commit()
    await db.refresh(payment)

    return {
        "razorpay_order_id": razorpay_order_id,
        "amount": int(order.total * 100),
        "currency": "INR",
        "key_id": RAZORPAY_KEY_ID if RAZORPAY_KEY_ID and "placeholder" not in RAZORPAY_KEY_ID else "",
        "payment_id": payment.id,
        "order_id": order.id,
    }


@router.post("/verify")
async def verify_payment(request: RazorpayVerifyRequest, db: AsyncSession = Depends(get_db)):
    """Verify Razorpay payment signature and update order/payment status."""
    # Find payment
    payment_result = await db.execute(
        select(Payment).where(Payment.razorpay_order_id == request.razorpay_order_id)
    )
    payment = payment_result.scalar_one_or_none()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    # Idempotency
    if payment.status == "success":
        return {"status": "success", "message": "Payment already verified"}

    # Verify signature
    is_valid = verify_razorpay_signature(
        request.razorpay_order_id, request.razorpay_payment_id, request.razorpay_signature
    )

    if not is_valid:
        payment.status = "failed"
        payment.failure_reason = "Invalid payment signature"
        order_result = await db.execute(select(Order).where(Order.id == payment.order_id))
        order = order_result.scalar_one_or_none()
        if order:
            order.status = "payment_failed"
            order.payment_status = "failed"

        audit = AuditLog(
            action="PAYMENT_FAILED",
            description=f"Payment verification failed for order {payment.order_id}",
            event_type="payment",
            related_entity=payment.order_id,
            final_status="failed",
        )
        db.add(audit)
        await db.commit()
        raise HTTPException(status_code=400, detail="Payment verification failed")

    # Payment successful - update everything
    payment.status = "success"
    payment.razorpay_payment_id = request.razorpay_payment_id
    payment.razorpay_signature = request.razorpay_signature

    # Update order
    order_result = await db.execute(select(Order).where(Order.id == payment.order_id))
    order = order_result.scalar_one_or_none()
    if order:
        order.status = "success"
        order.payment_status = "paid"
        order.razorpay_payment_id = request.razorpay_payment_id

        # Update inventory
        if order.cart_id:
            items_result = await db.execute(
                select(CartItem).where(CartItem.cart_id == order.cart_id)
            )
            cart_items = items_result.scalars().all()
            for ci in cart_items:
                product_result = await db.execute(select(Product).where(Product.id == ci.product_id))
                product = product_result.scalar_one_or_none()
                if product:
                    product.stock = max(0, product.stock - ci.quantity)
                    product.sales = (product.sales or 0) + ci.quantity
                    product.revenue = (product.revenue or 0) + (product.price * ci.quantity)

    # Audit
    audit = AuditLog(
        action="PAYMENT_SUCCESSFUL",
        description=f"Payment verified for order {payment.order_id}, amount: {payment.amount}",
        event_type="payment",
        related_entity=payment.order_id,
        financial_impact=payment.amount,
        final_status="success",
    )
    db.add(audit)
    await db.commit()

    return {"status": "success", "message": "Payment verified successfully"}


@router.post("/demo-success/{order_id}")
async def demo_payment_success(order_id: str, db: AsyncSession = Depends(get_db)):
    """Simulate a successful payment for demo/testing."""
    order_result = await db.execute(select(Order).where(Order.id == order_id))
    order = order_result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Find or create payment
    payment_result = await db.execute(
        select(Payment).where(Payment.order_id == order_id)
    )
    payment = payment_result.scalar_one_or_none()

    demo_payment_id = f"pay_demo_{uuid.uuid4().hex[:8]}"
    demo_signature = f"sig_demo_{uuid.uuid4().hex[:8]}"

    if payment:
        payment.status = "success"
        payment.razorpay_payment_id = demo_payment_id
        payment.razorpay_signature = demo_signature
    else:
        payment = Payment(
            order_id=order.id, amount=order.total, currency="INR", status="success",
            razorpay_order_id=order.razorpay_order_id or f"order_demo_{uuid.uuid4().hex[:8]}",
            razorpay_payment_id=demo_payment_id, razorpay_signature=demo_signature,
        )
        db.add(payment)

    # Update order
    order.status = "success"
    order.payment_status = "paid"
    order.razorpay_payment_id = demo_payment_id

    # Update inventory
    if order.cart_id:
        items_result = await db.execute(
            select(CartItem).where(CartItem.cart_id == order.cart_id)
        )
        cart_items = items_result.scalars().all()
        for ci in cart_items:
            product_result = await db.execute(select(Product).where(Product.id == ci.product_id))
            product = product_result.scalar_one_or_none()
            if product:
                product.stock = max(0, product.stock - ci.quantity)
                product.sales = (product.sales or 0) + ci.quantity
                product.revenue = (product.revenue or 0) + (product.price * ci.quantity)

    audit = AuditLog(
        action="PAYMENT_SUCCESSFUL",
        description=f"Demo payment completed for order {order.id}, amount: {order.total}",
        event_type="payment",
        related_entity=order.id,
        financial_impact=order.total,
        final_status="success",
    )
    db.add(audit)
    await db.commit()

    return {"status": "success", "payment_id": payment.id, "order_id": order_id}


@router.post("/demo-fail/{payment_id}", response_model=PaymentResponse)
async def demo_fail_payment(payment_id: str, db: AsyncSession = Depends(get_db)):
    """Simulate a payment failure for demo purposes."""
    result = await db.execute(select(Payment).where(Payment.id == payment_id))
    payment = result.scalar_one_or_none()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    if payment.status not in ("initiated", "created"):
        raise HTTPException(status_code=400, detail=f"Cannot fail payment in status: {payment.status}")

    payment.status = "failed"
    payment.failure_reason = "Demo simulated failure: Insufficient funds"

    order_result = await db.execute(select(Order).where(Order.id == payment.order_id))
    order = order_result.scalar_one_or_none()
    if order:
        order.status = "payment_failed"
        order.payment_status = "failed"

    await db.commit()
    await db.refresh(payment)

    return PaymentResponse(
        id=payment.id, order_id=payment.order_id, amount=payment.amount,
        currency=payment.currency, status=payment.status,
        razorpay_order_id=payment.razorpay_order_id,
        razorpay_payment_id=payment.razorpay_payment_id,
        failure_reason=payment.failure_reason, created_at=payment.created_at
    )


@router.get("/{payment_id}", response_model=PaymentResponse)
async def get_payment(payment_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Payment).where(Payment.id == payment_id))
    payment = result.scalar_one_or_none()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return PaymentResponse(
        id=payment.id, order_id=payment.order_id, amount=payment.amount,
        currency=payment.currency, status=payment.status,
        razorpay_order_id=payment.razorpay_order_id,
        razorpay_payment_id=payment.razorpay_payment_id,
        failure_reason=payment.failure_reason, created_at=payment.created_at
    )
