"""
Approval endpoints with proper validation.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.database import get_db
from models.models import Approval, Order
from pydantic import BaseModel
from typing import Optional

router = APIRouter()


class ApprovalResponse(BaseModel):
    id: str
    order_id: str
    status: str
    token: Optional[str]


@router.get("/{approval_id}", response_model=ApprovalResponse)
async def get_approval(approval_id: str, db: AsyncSession = Depends(get_db)):
    """Get approval details."""
    result = await db.execute(select(Approval).where(Approval.id == approval_id))
    approval = result.scalar_one_or_none()
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")
    return approval


@router.post("/{approval_id}/approve")
async def approve(approval_id: str, db: AsyncSession = Depends(get_db)):
    """Approve a pending payment."""
    result = await db.execute(select(Approval).where(Approval.id == approval_id))
    approval = result.scalar_one_or_none()
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")
    if approval.status != "pending":
        raise HTTPException(status_code=400, detail=f"Approval already processed: {approval.status}")

    # Verify the order is in approval_pending state
    order_result = await db.execute(select(Order).where(Order.id == approval.order_id))
    order = order_result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.status != "approval_pending":
        raise HTTPException(status_code=400, detail=f"Order is not in approval_pending state: {order.status}")

    approval.status = "approved"
    approval.approved_by = "user"
    order.status = "approved"

    await db.commit()
    return {"status": "approved", "order_id": approval.order_id}


@router.post("/{approval_id}/reject")
async def reject(approval_id: str, db: AsyncSession = Depends(get_db)):
    """Reject a pending payment."""
    result = await db.execute(select(Approval).where(Approval.id == approval_id))
    approval = result.scalar_one_or_none()
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")

    approval.status = "rejected"

    order_result = await db.execute(select(Order).where(Order.id == approval.order_id))
    order = order_result.scalar_one_or_none()
    if order:
        order.status = "CANCELLED"
        order.payment_status = "CANCELLED"

    await db.commit()
    return {"status": "rejected", "order_id": approval.order_id}
