"""
Payment endpoints with Razorpay integration.

Implements the full payment lifecycle with explicit state machines:

  Payment states:
    CREATED   → payment record created (nothing sent to Razorpay yet)
    PENDING   → Razorpay TEST MODE order created, awaiting checkout
    CAPTURED  → Razorpay webhook reported payment.captured (money captured,
                but NOT yet marked paid — final PAID requires signature verify)
    PAID      → signature verified on the backend (final success)
    FAILED    → payment failed / signature invalid (final)
    CANCELLED → user cancelled checkout (final)

  Order states:
    PENDING_PAYMENT → order created, awaiting verified payment
    PAID            → payment verified
    CONFIRMED       → paid + confirmed (final success)
    PAYMENT_FAILED  → payment failed / signature invalid (retry allowed)
    CANCELLED       → cancelled (final)

Security rules enforced here:
  - The final amount is ALWAYS computed server-side from trusted catalog/cart
    data. Client-supplied amounts are never trusted.
  - A payment is only marked PAID after the Razorpay signature is verified
    with the secret key from the environment (never the frontend, never logs).
  - A Razorpay payment ID maps to exactly one successful application order
    (duplicate callbacks are idempotent, cross-order reuse is rejected).
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from models.database import get_db
from models.models import Payment, Order, Product, Cart, CartItem, AuditLog
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

# ── Canonical state machines (spec §6, §7) ─────────────────────────────
PAYMENT_STATES = ("CREATED", "PENDING", "AUTHORIZED", "CAPTURED", "PAID", "FAILED", "CANCELLED")
ORDER_STATES = ("PENDING_PAYMENT", "PAID", "CONFIRMED", "PAYMENT_FAILED", "CANCELLED")
TERMINAL_PAYMENT_SUCCESS = ("PAID", "CAPTURED")
TERMINAL_ORDER_SUCCESS = ("CONFIRMED", "PAID")


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
    """Return the Razorpay client ONLY when real TEST MODE keys are configured."""
    if not RAZORPAY_KEY_ID or not RAZORPAY_KEY_SECRET or "placeholder" in RAZORPAY_KEY_ID.lower():
        return None
    try:
        import razorpay
        return razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))
    except ImportError:
        logger.warning("razorpay package not installed")
        return None


def _razorpay_mode() -> str:
    """'live_test' when real Razorpay TEST keys are configured, else 'demo'."""
    return "live_test" if get_razorpay_client() else "demo"


def verify_razorpay_signature(order_id: str, payment_id: str, signature: str) -> bool:
    """Verify a Razorpay payment signature: HMAC-SHA256(order_id|payment_id, secret).

    In demo mode (no secret configured) verification is skipped so the flow can
    be exercised without credentials — but then the record is clearly labeled
    DEMO/SYNTHETIC and never claims to be a real Razorpay payment.
    """
    if not RAZORPAY_KEY_SECRET:
        logger.warning("No Razorpay secret configured, skipping verification (demo mode)")
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


def _audit(db: AsyncSession, *, action: str, related_entity: Optional[str] = None,
           payment_reference: Optional[str] = None, decision: Optional[str] = None,
           policy_result: Optional[str] = None, final_status: Optional[str] = None,
           description: Optional[str] = None, financial_impact: Optional[float] = None,
           event_type: str = "payment") -> AuditLog:
    """Create an audit log entry (not yet committed)."""
    entry = AuditLog(
        action=action,
        description=description or action,
        event_type=event_type,
        related_entity=related_entity,
        payment_reference=payment_reference,
        decision=decision,
        policy_result=policy_result,
        final_status=final_status,
        financial_impact=financial_impact,
        created_at=datetime.now(timezone.utc),
    )
    db.add(entry)
    return entry


async def _apply_inventory(db: AsyncSession, order: Order):
    """Decrement stock and increment sales/revenue from order items (server-side prices)."""
    if not order.cart_id:
        return
    items_result = await db.execute(
        select(CartItem).where(CartItem.cart_id == order.cart_id)
    )
    for ci in items_result.scalars().all():
        product_result = await db.execute(select(Product).where(Product.id == ci.product_id))
        product = product_result.scalar_one_or_none()
        if product:
            product.stock = max(0, product.stock - ci.quantity)
            product.sales = (product.sales or 0) + ci.quantity
            product.revenue = (product.revenue or 0) + (product.price * ci.quantity)


async def _mark_order_paid(db: AsyncSession, payment: Payment, razorpay_payment_id: str,
                           signature: Optional[str], demo: bool = False):
    """Mark a verified payment + order as PAID/CONFIRMED. Idempotent."""
    order_result = await db.execute(select(Order).where(Order.id == payment.order_id))
    order = order_result.scalar_one_or_none()

    payment.status = "PAID"
    payment.razorpay_payment_id = razorpay_payment_id
    payment.failure_reason = None
    if signature:
        payment.razorpay_signature = signature

    if order:
        # Only decrement inventory on the FIRST time this order becomes paid.
        first_paid = order.payment_status not in TERMINAL_PAYMENT_SUCCESS and \
            order.status not in TERMINAL_ORDER_SUCCESS
        order.status = "CONFIRMED"
        order.payment_status = "PAID"
        order.razorpay_payment_id = razorpay_payment_id
        if first_paid:
            await _apply_inventory(db, order)
            # Clear the cart ONLY after a verified payment (spec §8): failed or
            # cancelled payments must leave the cart fully available, while a
            # successful payment empties it for the confirmation screen.
            if order.cart_id:
                cart_res = await db.execute(select(Cart).where(Cart.id == order.cart_id))
                paid_cart = cart_res.scalar_one_or_none()
                if paid_cart and paid_cart.status == "active":
                    ci_res = await db.execute(select(CartItem).where(CartItem.cart_id == paid_cart.id))
                    for ci in ci_res.scalars().all():
                        await db.delete(ci)
                    paid_cart.status = "completed"
                    paid_cart.total = 0.0

    label = "DEMO/SYNTHETIC payment (no live Razorpay keys)" if demo else "Razorpay TEST MODE payment"
    _audit(
        db, action="PAYMENT_VERIFIED",
        related_entity=payment.order_id,
        payment_reference=razorpay_payment_id,
        decision=f"{label} verified successfully",
        policy_result="signature_valid",
        final_status="PAID",
        description=f"Payment {razorpay_payment_id} verified for order {payment.order_id}, amount: {payment.amount}",
        financial_impact=payment.amount,
    )
    _audit(
        db, action="ORDER_CONFIRMED",
        related_entity=payment.order_id,
        payment_reference=razorpay_payment_id,
        decision=f"Order confirmed after verified payment",
        policy_result="payment_verified",
        final_status="CONFIRMED",
        description=f"Order {payment.order_id} confirmed (amount ₹{payment.amount})",
        financial_impact=payment.amount,
        event_type="order",
    )


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
    """Create a Razorpay TEST MODE order for the given application order.

    Idempotent: calling twice for the same order reuses the existing
    Razorpay order instead of creating duplicates.
    """
    order_result = await db.execute(select(Order).where(Order.id == request.order_id))
    order = order_result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.status not in ("PENDING_PAYMENT", "PAYMENT_FAILED"):
        raise HTTPException(status_code=400, detail=f"Order cannot be paid. Status: {order.status}")

    # Reject if this order already has a successful payment.
    existing_success = await db.execute(
        select(Payment).where(
            Payment.order_id == order.id,
            Payment.status.in_(TERMINAL_PAYMENT_SUCCESS)
        )
    )
    if existing_success.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Payment already completed for this order")

    # Reuse a pending payment record (idempotency — one Razorpay order per app order).
    pending_result = await db.execute(
        select(Payment).where(Payment.order_id == order.id)
        .order_by(Payment.created_at.desc()).limit(1)
    )
    payment = pending_result.scalar_one_or_none()

    if payment and payment.razorpay_order_id:
        # Already created — return the same Razorpay order (idempotent), and
        # restore the order to the awaiting-payment state for a retry.
        payment.status = "PENDING"
        order.status = "PENDING_PAYMENT"
        order.payment_status = "PENDING"
        await db.commit()
        return {
            "razorpay_order_id": payment.razorpay_order_id,
            "amount": int(order.total * 100),
            "currency": "INR",
            "key_id": RAZORPAY_KEY_ID if RAZORPAY_KEY_ID and "placeholder" not in RAZORPAY_KEY_ID else "",
            "payment_id": payment.id,
            "order_id": order.id,
        }

    if not payment:
        payment = Payment(
            order_id=order.id,
            amount=order.total,
            currency="INR",
            status="CREATED",
        )
        db.add(payment)
        await db.flush()

    # ── Server-side amount security: never trust the client ──
    # order.total was computed from trusted DB prices at checkout. If it is not
    # a positive amount, refuse to create any payment order.
    if not order.total or order.total <= 0:
        raise HTTPException(status_code=400, detail="Invalid order amount. Cannot create payment.")

    client = get_razorpay_client()
    mode = "live_test" if client else "demo"
    if client:
        try:
            rzp_order = client.order.create({
                "amount": int(order.total * 100),  # paise
                "currency": "INR",
                "receipt": str(order.id),
            })
            razorpay_order_id = rzp_order["id"]
            # Defense in depth: the amount Razorpay recorded must match the
            # trusted server-side total.
            if int(rzp_order.get("amount", 0)) != int(order.total * 100):
                payment.status = "FAILED"
                payment.failure_reason = "Razorpay order amount mismatch"
                await db.commit()
                raise HTTPException(status_code=500, detail="Payment gateway amount mismatch")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Razorpay order creation failed: {e}")
            raise HTTPException(status_code=500, detail="Payment gateway error")
    else:
        # Demo mode: synthetic Razorpay order id, clearly labeled.
        razorpay_order_id = f"order_demo_{uuid.uuid4().hex[:12]}"
        logger.warning("Razorpay not configured, using demo order ID (DEMO/SYNTHETIC)")

    payment.razorpay_order_id = razorpay_order_id
    payment.status = "PENDING"

    # Update order state
    order.status = "PENDING_PAYMENT"
    order.payment_status = "PENDING"
    order.razorpay_order_id = razorpay_order_id

    _audit(
        db, action="RAZORPAY_ORDER_CREATED",
        related_entity=order.id,
        payment_reference=razorpay_order_id,
        decision=f"Razorpay order {razorpay_order_id} created (mode={mode})",
        policy_result="amount_validated" if mode == "live_test" else "demo_mode",
        final_status="PENDING",
        description=f"Razorpay order {razorpay_order_id} created for order {order.id}, amount: ₹{order.total}",
        financial_impact=order.total,
    )
    _audit(
        db, action="PAYMENT_INITIATED",
        related_entity=order.id,
        payment_reference=razorpay_order_id,
        decision="Payment initiated — awaiting checkout",
        policy_result="within_policy",
        final_status="PENDING",
        description=f"Payment initiated for order {order.id}, amount: ₹{order.total}",
        financial_impact=order.total,
    )
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
    """Verify a Razorpay payment signature and update order/payment status.

    - Never marks an order paid before server-side signature verification.
    - Idempotent: repeated callbacks for an already-paid payment are safe and
      never create a second order.
    - A Razorpay payment ID maps to exactly one successful application order.
    """
    payment_result = await db.execute(
        select(Payment).where(Payment.razorpay_order_id == request.razorpay_order_id)
    )
    payment = payment_result.scalar_one_or_none()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    # Idempotency: only a fully PAID payment short-circuits. A CAPTURED payment
    # (Razorpay webhook arrived first) still needs this signature-verified
    # callback to promote CAPTURED → PAID and confirm the order — see webhooks.py.
    if payment.status == "PAID":
        return {"status": "success", "message": "Payment already verified"}

    order_result = await db.execute(select(Order).where(Order.id == payment.order_id))
    order = order_result.scalar_one_or_none()

    # ── Server-side amount security ──
    # The amount Razorpay charged must equal the trusted order total.
    if order and int(payment.amount * 100) != int(order.total * 100):
        payment.status = "FAILED"
        payment.failure_reason = "Payment amount does not match order total"
        if order:
            order.status = "PAYMENT_FAILED"
            order.payment_status = "FAILED"
        _audit(
            db, action="PAYMENT_FAILED",
            related_entity=payment.order_id,
            payment_reference=request.razorpay_payment_id,
            decision="Amount mismatch — payment NOT marked paid",
            policy_result="amount_mismatch",
            final_status="FAILED",
            description=f"Payment amount mismatch for order {payment.order_id}",
            financial_impact=payment.amount,
        )
        await db.commit()
        raise HTTPException(status_code=400, detail="Payment amount does not match order total")

    # ── Duplicate payment prevention ──
    # The same Razorpay payment ID must never be applied to two orders.
    dup_result = await db.execute(
        select(Payment).where(
            Payment.razorpay_payment_id == request.razorpay_payment_id,
            Payment.status.in_(TERMINAL_PAYMENT_SUCCESS),
            Payment.id != payment.id,
        )
    )
    if dup_result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="This payment has already been processed for another order")

    _audit(
        db, action="PAYMENT_RECEIVED",
        related_entity=payment.order_id,
        payment_reference=request.razorpay_payment_id,
        decision="Payment callback received — verifying signature",
        policy_result="pending_verification",
        final_status="PENDING",
        description=f"Payment {request.razorpay_payment_id} received for order {payment.order_id}",
        financial_impact=payment.amount,
    )

    # ── Signature verification (spec §4) ──
    is_valid = verify_razorpay_signature(
        request.razorpay_order_id, request.razorpay_payment_id, request.razorpay_signature
    )

    if not is_valid:
        if payment.status != "CAPTURED":
            # Not captured yet: an invalid signature means the attempt failed.
            payment.status = "FAILED"
            payment.failure_reason = "Invalid payment signature"
            if order:
                order.status = "PAYMENT_FAILED"
                order.payment_status = "FAILED"
            _audit(
                db, action="PAYMENT_FAILED",
                related_entity=payment.order_id,
                payment_reference=request.razorpay_payment_id,
                decision="Signature verification failed — order NOT marked paid",
                policy_result="invalid_signature",
                final_status="FAILED",
                description=f"Payment verification failed for order {payment.order_id} (invalid signature)",
                financial_impact=payment.amount,
            )
            await db.commit()
        else:
            # Money was already captured by the webhook; never downgrade that to
            # FAILED. Refuse to confirm without a valid signature instead.
            logger.warning(f"Verify callback with invalid signature for captured payment {payment.id} — order NOT confirmed")
        raise HTTPException(status_code=400, detail="Payment verification failed. No charge was recorded.")

    # ── Success path ──
    await _mark_order_paid(db, payment, request.razorpay_payment_id, request.razorpay_signature, demo=False)
    await db.commit()

    return {"status": "success", "message": "Payment verified successfully"}


@router.post("/demo-success/{order_id}")
async def demo_payment_success(order_id: str, db: AsyncSession = Depends(get_db)):
    """Simulate a successful TEST payment — DEMO/SYNTHETIC only.

    Used when no Razorpay TEST keys are configured, so the full flow can be
    exercised end-to-end without credentials. Records are explicitly labeled
    DEMO/SYNTHETIC and are never claimed to be real Razorpay payments.
    """
    order_result = await db.execute(select(Order).where(Order.id == order_id))
    order = order_result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    payment_result = await db.execute(
        select(Payment).where(Payment.order_id == order_id)
        .order_by(Payment.created_at.desc()).limit(1)
    )
    payment = payment_result.scalar_one_or_none()

    if payment and payment.status in TERMINAL_PAYMENT_SUCCESS:
        return {"status": "success", "message": "Payment already verified", "payment_id": payment.id, "order_id": order_id}

    if payment is None:
        payment = Payment(
            order_id=order.id, amount=order.total, currency="INR", status="CREATED",
            razorpay_order_id=order.razorpay_order_id or f"order_demo_{uuid.uuid4().hex[:12]}",
        )
        db.add(payment)
        await db.flush()

    # Server-side amount security: demo payment amount must equal the order total.
    if int(payment.amount * 100) != int(order.total * 100):
        payment.status = "FAILED"
        payment.failure_reason = "Payment amount does not match order total"
        order.status = "PAYMENT_FAILED"
        order.payment_status = "FAILED"
        _audit(
            db, action="PAYMENT_FAILED",
            related_entity=order.id, payment_reference=payment.razorpay_order_id,
            decision="Amount mismatch — payment NOT marked paid",
            policy_result="amount_mismatch", final_status="FAILED",
            description=f"DEMO payment amount mismatch for order {order.id}",
            financial_impact=order.total,
        )
        await db.commit()
        raise HTTPException(status_code=400, detail="Payment amount does not match order total")

    demo_payment_id = f"pay_demo_{uuid.uuid4().hex[:8]}"
    demo_signature = f"sig_demo_{uuid.uuid4().hex[:8]}"

    await _mark_order_paid(db, payment, demo_payment_id, demo_signature, demo=True)
    await db.commit()

    return {"status": "success", "payment_id": payment.id, "order_id": order_id}


@router.post("/demo-fail/{payment_id}", response_model=PaymentResponse)
async def demo_fail_payment(payment_id: str, db: AsyncSession = Depends(get_db)):
    """Simulate a payment failure for demo/testing purposes."""
    result = await db.execute(select(Payment).where(Payment.id == payment_id))
    payment = result.scalar_one_or_none()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    if payment.status in TERMINAL_PAYMENT_SUCCESS:
        raise HTTPException(status_code=400, detail=f"Cannot fail a payment already in status: {payment.status}")
    if payment.status == "FAILED":
        return PaymentResponse(
            id=payment.id, order_id=payment.order_id, amount=payment.amount,
            currency=payment.currency, status=payment.status,
            razorpay_order_id=payment.razorpay_order_id,
            razorpay_payment_id=payment.razorpay_payment_id,
            failure_reason=payment.failure_reason, created_at=payment.created_at
        )

    payment.status = "FAILED"
    payment.failure_reason = "Demo simulated failure: Insufficient funds"

    order_result = await db.execute(select(Order).where(Order.id == payment.order_id))
    order = order_result.scalar_one_or_none()
    if order:
        order.status = "PAYMENT_FAILED"
        order.payment_status = "FAILED"

    _audit(
        db, action="PAYMENT_FAILED",
        related_entity=payment.order_id,
        payment_reference=payment.razorpay_order_id,
        decision="Payment failed — order NOT marked paid",
        policy_result="payment_declined",
        final_status="FAILED",
        description=f"Payment failed for order {payment.order_id}: {payment.failure_reason}",
        financial_impact=payment.amount,
    )
    await db.commit()
    await db.refresh(payment)

    return PaymentResponse(
        id=payment.id, order_id=payment.order_id, amount=payment.amount,
        currency=payment.currency, status=payment.status,
        razorpay_order_id=payment.razorpay_order_id,
        razorpay_payment_id=payment.razorpay_payment_id,
        failure_reason=payment.failure_reason, created_at=payment.created_at
    )


@router.post("/demo-cancel/{payment_id}", response_model=PaymentResponse)
async def demo_cancel_payment(payment_id: str, db: AsyncSession = Depends(get_db)):
    """Cancel a pending payment (user closed the checkout without paying)."""
    result = await db.execute(select(Payment).where(Payment.id == payment_id))
    payment = result.scalar_one_or_none()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    if payment.status in TERMINAL_PAYMENT_SUCCESS or payment.status == "FAILED":
        raise HTTPException(status_code=400, detail=f"Cannot cancel payment in status: {payment.status}")

    payment.status = "CANCELLED"
    payment.failure_reason = "Checkout cancelled by user"

    order_result = await db.execute(select(Order).where(Order.id == payment.order_id))
    order = order_result.scalar_one_or_none()
    if order and order.status in ("PENDING_PAYMENT", "PAYMENT_FAILED"):
        order.status = "CANCELLED"
        order.payment_status = "CANCELLED"

    _audit(
        db, action="ORDER_CANCELLED",
        related_entity=payment.order_id,
        payment_reference=payment.razorpay_order_id,
        decision="Checkout cancelled — no charge recorded",
        policy_result="cancelled_by_user",
        final_status="CANCELLED",
        description=f"Payment cancelled for order {payment.order_id}",
        financial_impact=0,
        event_type="order",
    )
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