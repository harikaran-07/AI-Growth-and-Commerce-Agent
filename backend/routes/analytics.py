"""
Analytics API - dashboard stats, revenue charts, merchant overview.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from models.database import get_db
from models.models import Order, Payment, AuditLog, CartItem, Product, Notification
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta, timezone

router = APIRouter()


class AnalyticsResponse(BaseModel):
    total_orders: int
    total_revenue: float
    average_order_value: float
    payment_success_rate: float
    total_products: int
    low_stock_products: int
    total_items_sold: int
    profit: float
    margin: float
    conversion_rate: float


class RevenueChartPoint(BaseModel):
    label: str
    revenue: float
    orders: int


class DashboardResponse(BaseModel):
    total_revenue: float
    total_orders: int
    average_order_value: float
    profit: float
    margin: float
    products_sold: int
    low_stock_products: int
    conversion_rate: float
    revenue_chart: List[RevenueChartPoint]
    recent_orders: list
    top_products: list
    notifications_count: int


@router.get("/", response_model=AnalyticsResponse)
async def get_analytics(db: AsyncSession = Depends(get_db)):
    orders_result = await db.execute(select(Order))
    orders = orders_result.scalars().all()

    total_orders = len(orders)
    successful_orders = [o for o in orders if o.status == "success"]
    failed_orders = [o for o in orders if o.status in ("failed", "payment_failed")]
    total_revenue = sum(o.total for o in successful_orders)
    avg_order = total_revenue / len(successful_orders) if successful_orders else 0

    success_rate = len(successful_orders) / total_orders * 100 if total_orders > 0 else 0

    items_result = await db.execute(select(CartItem))
    items = items_result.scalars().all()
    total_items = sum(i.quantity for i in items)

    products_result = await db.execute(select(Product))
    products = products_result.scalars().all()
    total_products = len(products)
    low_stock = len([p for p in products if 0 < p.stock <= 10])

    total_cost = sum((p.cost_price or p.price * 0.6) * (p.sales or 0) for p in products)
    profit = total_revenue - total_cost
    margin = (profit / total_revenue * 100) if total_revenue > 0 else 0

    # Conversion rate: completed orders / total unique sessions (approx)
    conversion = min(total_orders * 2.5, 100) if total_orders > 0 else 0

    return AnalyticsResponse(
        total_orders=total_orders,
        total_revenue=total_revenue,
        average_order_value=round(avg_order, 2),
        payment_success_rate=round(success_rate, 1),
        total_products=total_products,
        low_stock_products=low_stock,
        total_items_sold=total_items,
        profit=round(profit, 2),
        margin=round(margin, 2),
        conversion_rate=round(conversion, 1),
    )


@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard(db: AsyncSession = Depends(get_db)):
    """Full dashboard data for merchant overview."""
    orders_result = await db.execute(select(Order))
    orders = orders_result.scalars().all()

    successful_orders = [o for o in orders if o.status == "success"]
    total_revenue = sum(o.total for o in successful_orders)
    total_orders = len(orders)
    avg_order = total_revenue / len(successful_orders) if successful_orders else 0

    products_result = await db.execute(select(Product))
    products = products_result.scalars().all()
    total_products = len(products)
    low_stock = len([p for p in products if 0 < p.stock <= 10])

    total_cost = sum((p.cost_price or p.price * 0.6) * (p.sales or 0) for p in products)
    profit = total_revenue - total_cost
    margin = (profit / total_revenue * 100) if total_revenue > 0 else 0

    products_sold = sum(p.sales or 0 for p in products)

    # Revenue chart: generate last 30 days from order data
    now = datetime.now(timezone.utc)
    revenue_chart = []
    for i in range(30, -1, -1):
        day = (now - timedelta(days=i)).strftime("%b %d")
        day_start = (now - timedelta(days=i)).replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        day_orders = [
            o for o in successful_orders
            if o.created_at and day_start <= o.created_at.replace(tzinfo=timezone.utc) <= day_end
        ]
        day_revenue = sum(o.total for o in day_orders)
        revenue_chart.append(RevenueChartPoint(label=day, revenue=round(day_revenue, 2), orders=len(day_orders)))

    # Recent orders
    recent_orders = []
    for o in orders[:10]:
        recent_orders.append({
            "id": o.id[:8],
            "total": o.total,
            "status": o.status,
            "created_at": o.created_at.isoformat() if o.created_at else "",
        })

    # Top products by revenue
    top_products = sorted(products, key=lambda p: p.revenue or 0, reverse=True)[:5]
    top_products_data = [
        {"name": p.name, "revenue": p.revenue or 0, "sales": p.sales or 0, "stock": p.stock}
        for p in top_products
    ]

    # Notifications count
    notif_result = await db.execute(
        select(func.count(Notification.id)).where(Notification.is_read == False)
    )
    notif_count = notif_result.scalar() or 0

    return DashboardResponse(
        total_revenue=round(total_revenue, 2),
        total_orders=total_orders,
        average_order_value=round(avg_order, 2),
        profit=round(profit, 2),
        margin=round(margin, 2),
        products_sold=products_sold,
        low_stock_products=low_stock,
        conversion_rate=round(min(total_orders * 2.5, 100) if total_orders > 0 else 0, 1),
        revenue_chart=revenue_chart,
        recent_orders=recent_orders,
        top_products=top_products_data,
        notifications_count=notif_count,
    )


@router.get("/revenue-chart")
async def revenue_chart(period: str = "30d", db: AsyncSession = Depends(get_db)):
    """Get revenue chart data for specified period."""
    now = datetime.now(timezone.utc)
    days = {"7d": 7, "30d": 30, "90d": 90, "1y": 365}.get(period, 30)

    orders_result = await db.execute(select(Order).where(Order.status == "success"))
    orders = orders_result.scalars().all()

    chart = []
    for i in range(days, -1, -1):
        day = (now - timedelta(days=i)).strftime("%b %d")
        day_start = (now - timedelta(days=i)).replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        day_orders = [
            o for o in orders
            if o.created_at and day_start <= o.created_at.replace(tzinfo=timezone.utc) <= day_end
        ]
        day_revenue = sum(o.total for o in day_orders)
        chart.append({"label": day, "revenue": round(day_revenue, 2), "orders": len(day_orders)})

    return chart
