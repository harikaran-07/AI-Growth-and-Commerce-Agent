from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.database import get_db
from models.models import Policy
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

class PolicyResponse(BaseModel):
    id: str
    max_transaction_amount: float
    max_discount_percentage: float
    payment_requires_approval: bool
    max_retry_attempts: int

class PolicyUpdate(BaseModel):
    max_transaction_amount: Optional[float] = None
    max_discount_percentage: Optional[float] = None
    payment_requires_approval: Optional[bool] = None
    max_retry_attempts: Optional[int] = None

@router.get("/", response_model=PolicyResponse)
async def get_policy(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Policy).limit(1))
    policy = result.scalar_one_or_none()
    if not policy:
        policy = Policy(
            max_transaction_amount=3000,
            max_discount_percentage=10,
            payment_requires_approval=True,
            max_retry_attempts=1
        )
        db.add(policy)
        await db.commit()
        await db.refresh(policy)
    return policy

@router.put("/", response_model=PolicyResponse)
async def update_policy(update: PolicyUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Policy).limit(1))
    policy = result.scalar_one_or_none()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    
    if update.max_transaction_amount is not None:
        policy.max_transaction_amount = update.max_transaction_amount
    if update.max_discount_percentage is not None:
        policy.max_discount_percentage = update.max_discount_percentage
    if update.payment_requires_approval is not None:
        policy.payment_requires_approval = update.payment_requires_approval
    if update.max_retry_attempts is not None:
        policy.max_retry_attempts = update.max_retry_attempts
    
    await db.commit()
    await db.refresh(policy)
    return policy
