from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.database import get_db
from models.models import Payment, Order
from pydantic import BaseModel
from typing import List, Optional
import os
import razorpay
import uuid

router = APIRouter()

RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID", "rzp_test_placeholder")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "placeholder_secret")

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

def get_razorpay_client():
    return razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))

@router.get("/", response_model=List[PaymentResponse])
async def get_all_payments(limit: int = 100, db: AsyncSession = Depends(get_db)):
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
            failure_reason=p.failure_reason
        ) for p in payments
    ]

@router.post("/", response_model=PaymentResponse)
async def create_payment(payment: PaymentCreate, db: AsyncSession = Depends(get_db)):
    order_result = await db.execute(select(Order).where(Order.id == payment.order_id))
    order = order_result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.status != "approved":
        raise HTTPException(status_code=400, detail="Order not approved")
    
    existing_payment_result = await db.execute(
        select(Payment).where(Payment.order_id == payment.order_id, Payment.status == "success")
    )
    existing = existing_payment_result.scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Payment already completed")
    
    try:
        client = get_razorpay_client()
        razorpay_order = client.order.create({
            "amount": int(order.total * 100),
            "currency": "INR",
            "receipt": str(order.id),
        })
        razorpay_order_id = razorpay_order["id"]
        status = "initiated"
    except Exception as e:
        razorpay_order_id = f"fail_{uuid.uuid4().hex[:8]}"
        status = "failed"
    
    payment_record = Payment(
        order_id=payment.order_id,
        amount=order.total,
        currency="INR",
        status=status,
        razorpay_order_id=razorpay_order_id
    )
    db.add(payment_record)
    
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
        failure_reason=payment_record.failure_reason
    )

@router.get("/{payment_id}", response_model=PaymentResponse)
async def get_payment(payment_id: str, db: AsyncSession = Depends(get_db)):
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
        failure_reason=payment.failure_reason
    )

@router.post("/demo-fail/{payment_id}", response_model=PaymentResponse)
async def demo_fail_payment(payment_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Payment).where(Payment.id == payment_id))
    payment = result.scalar_one_or_none()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    payment.status = "failed"
    payment.failure_reason = "Demo failure: Insufficient funds (simulated for testing)"
    
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
        failure_reason=payment.failure_reason
    )
