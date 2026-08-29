from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from models.database import get_db
from models.models import Order, Payment, AuditLog, CartItem, Product
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

class AnalyticsResponse(BaseModel):
    total_orders: int
    total_revenue: float
    average_order_value: float
    upsell_conversions: int
    cross_sell_conversions: int
    payment_success_rate: float
    payment_failure_rate: float
    policy_blocks: int
    total_items_sold: int
    high_value_opportunities: int

@router.get("/", response_model=AnalyticsResponse)
async def get_analytics(db: AsyncSession = Depends(get_db)):
    orders_result = await db.execute(select(Order))
    orders = orders_result.scalars().all()
    
    total_orders = len(orders)
    successful_orders = [o for o in orders if o.status == "success"]
    failed_orders = [o for o in orders if o.status == "failed"]
    total_revenue = sum(o.total for o in successful_orders)
    avg_order = total_revenue / len(successful_orders) if successful_orders else 0
    
    success_rate = len(successful_orders) / total_orders * 100 if total_orders > 0 else 0
    failure_rate = len(failed_orders) / total_orders * 100 if total_orders > 0 else 0
    
    audit_result = await db.execute(
        select(AuditLog).where(AuditLog.action.like("%recommend%"))
    )
    recommend_logs = audit_result.scalars().all()
    upsell_count = sum(1 for l in recommend_logs if l.input_data and "upsell" in l.input_data.lower())
    cross_sell_count = sum(1 for l in recommend_logs if l.input_data and "cross-sell" in l.input_data.lower())
    
    policy_result = await db.execute(
        select(AuditLog).where(AuditLog.final_status == "policy_blocked")
    )
    policy_blocks = len(policy_result.scalars().all())
    
    items_result = await db.execute(select(CartItem))
    items = items_result.scalars().all()
    total_items = sum(i.quantity for i in items)
    
    high_value = len([o for o in orders if o.total > 2000])
    
    return AnalyticsResponse(
        total_orders=total_orders,
        total_revenue=total_revenue,
        average_order_value=avg_order,
        upsell_conversions=upsell_count,
        cross_sell_conversions=cross_sell_count,
        payment_success_rate=round(success_rate, 1),
        payment_failure_rate=round(failure_rate, 1),
        policy_blocks=policy_blocks,
        total_items_sold=total_items,
        high_value_opportunities=high_value
    )
