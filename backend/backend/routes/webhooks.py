from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.database import get_db
from models.models import Payment, Order
import os
import hashlib
import hmac

router = APIRouter()

RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "placeholder_secret")

@router.post("/razorpay")
async def razorpay_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    body = await request.body()
    signature = request.headers.get("X-Razorpay-Signature", "")
    
    expected_signature = hmac.new(
        RAZORPAY_KEY_SECRET.encode(),
        body,
        hashlib.sha256
    ).hexdigest()
    
    if signature != expected_signature:
        raise HTTPException(status_code=400, detail="Invalid signature")
    
    payload = await request.json()
    event = payload.get("event")
    
    if event == "payment.captured":
        payment_entity = payload["payload"]["payment"]["entity"]
        razorpay_payment_id = payment_entity["id"]
        razorpay_order_id = payment_entity["order_id"]
        
        payment_result = await db.execute(
            select(Payment).where(Payment.razorpay_order_id == razorpay_order_id)
        )
        payment = payment_result.scalar_one_or_none()
        if payment:
            payment.razorpay_payment_id = razorpay_payment_id
            payment.status = "success"
            
            order_result = await db.execute(
                select(Order).where(Order.id == payment.order_id)
            )
            order = order_result.scalar_one_or_none()
            if order:
                order.status = "success"
                order.razorpay_payment_id = razorpay_payment_id
            
            await db.commit()
    
    elif event == "payment.failed":
        payment_entity = payload["payload"]["payment"]["entity"]
        razorpay_order_id = payment_entity["order_id"]
        
        payment_result = await db.execute(
            select(Payment).where(Payment.razorpay_order_id == razorpay_order_id)
        )
        payment = payment_result.scalar_one_or_none()
        if payment:
            payment.status = "failed"
            payment.failure_reason = payment_entity.get("error_description", "Payment failed")
            
            order_result = await db.execute(
                select(Order).where(Order.id == payment.order_id)
            )
            order = order_result.scalar_one_or_none()
            if order:
                order.status = "failed"
            
            await db.commit()
    
    return {"status": "ok"}
