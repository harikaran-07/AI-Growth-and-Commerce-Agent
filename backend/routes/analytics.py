"""
Analytics API - dashboard stats, revenue charts, merchant overview.
Calculations based on REAL order/payment data, never fake/hardcoded values.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from models.database import get_db
from models.models import Order, Payment, AuditLog, CartItem, Product, Notification, OrderItem
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta, timezone
import math
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


def safe_float(val, default=0.0):
    """Safely convert any value to float, handling None/NaN/Inf/negative."""
    if val is None:
        return default
    try:
        v = float(val)
        if math.isnan(v) or math.isinf(v) or v < 0:
            return default
        return v
    except (TypeError, ValueError):
        return default


def safe_int(val, default=0):
    """Safely convert any value to int."""
    if val is None:
        return default
    try:
        v = int(val)
        return v if v >= 0 else default
    except (TypeError, ValueError):
        return default


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
    pending_orders: int
    completed_orders: int
    cancelled_orders: int
    refunds: int
    total_customers: int
    repeat_customers: int


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
    pending_orders: int
    completed_orders: int
    cancelled_orders: int
    total_customers: int
    best_sellers: list
    slow_movers: list
    low_stock_list: list
    category_revenue: list
    profit_analytics: dict


async def _get_successful_orders(db: AsyncSession) -> list:
    """Get all successful/paid orders."""
    result = await db.execute(
        select(Order).where(Order.status == "success")
    )
    return result.scalars().all()


async def _get_all_orders(db: AsyncSession) -> list:
    """Get all orders."""
    result = await db.execute(select(Order).order_by(Order.created_at.desc()))
    return result.scalars().all()


async def _get_order_items_for_order(db: AsyncSession, order_id: str) -> list:
    """Get order items for a specific order."""
    result = await db.execute(
        select(OrderItem).where(OrderItem.order_id == order_id)
    )
    return result.scalars().all()


async def _get_cart_items_for_cart(db: AsyncSession, cart_id: str) -> list:
    """Get cart items for a specific cart."""
    result = await db.execute(
        select(CartItem).where(CartItem.cart_id == cart_id)
    )
    return result.scalars().all()


async def _calculate_products_sold_from_orders(db: AsyncSession, orders: list) -> int:
    """Calculate products sold from actual order quantities in successful orders.
    
    ONLY counts quantity from successful/completed/paid orders.
    Never uses product.sales, product IDs, or any other fake data.
    """
    total_products_sold = 0
    for order in orders:
        items = await _get_order_items_for_order(db, order.id)
        for item in items:
            qty = safe_int(item.quantity, 0)
            total_products_sold += qty
    return total_products_sold


async def _calculate_revenue_from_orders(db: AsyncSession, orders: list) -> float:
    """Calculate revenue from successful paid orders only."""
    return sum(safe_float(o.total, 0) for o in orders)


async def _calculate_cogs_from_orders(db: AsyncSession, orders: list, products_map: dict) -> float:
    """Calculate Cost of Goods Sold from actual order items and product costs.
    
    COGS = SUM(product.cost_price * quantity) for all items in successful orders.
    If product.cost_price is missing, mark as "Cost data unavailable" and exclude.
    """
    total_cogs = 0.0
    for order in orders:
        items = await _get_order_items_for_order(db, order.id)
        for item in items:
            product = products_map.get(item.product_id)
            if product and product.cost_price is not None and product.cost_price > 0:
                qty = safe_int(item.quantity, 0)
                total_cogs += safe_float(product.cost_price, 0) * qty
    return total_cogs


@router.get("/", response_model=AnalyticsResponse)
async def get_analytics(db: AsyncSession = Depends(get_db)):
    """Full analytics with real data calculations."""
    
    # Get all orders
    all_orders = await _get_all_orders(db)
    successful_orders = [o for o in all_orders if o.status == "success"]
    failed_orders = [o for o in all_orders if o.status in ("failed", "payment_failed")]
    pending_orders = [o for o in all_orders if o.status in ("pending", "payment_initiated", "processing")]
    cancelled_orders = [o for o in all_orders if o.status == "cancelled"]
    refunded_orders = [o for o in all_orders if o.status == "refunded"]
    
    # Revenue from successful paid orders ONLY
    total_revenue = await _calculate_revenue_from_orders(db, successful_orders)
    
    # Orders count
    total_orders = len(all_orders)
    completed_count = len(successful_orders)
    
    # Average order value
    avg_order = safe_float(total_revenue / completed_count if completed_count > 0 else 0)
    
    # Payment success rate
    success_rate = (completed_count / total_orders * 100) if total_orders > 0 else 0
    
    # Products sold from actual order items
    products_sold = await _calculate_products_sold_from_orders(db, successful_orders)
    
    # Products and stock
    products_result = await db.execute(select(Product))
    products = products_result.scalars().all()
    products_map = {p.id: p for p in products}
    total_products = len(products)
    low_stock = len([p for p in products if 0 < p.stock <= 10])
    
    # COGS from actual product costs in orders
    total_cogs = await _calculate_cogs_from_orders(db, successful_orders, products_map)
    
    # Profit and margin
    gross_profit = safe_float(total_revenue - total_cogs)
    margin = safe_float((gross_profit / total_revenue * 100) if total_revenue > 0 else 0)
    
    # Conversion rate - completed orders / total orders (real conversion)
    conversion = safe_float((completed_count / total_orders * 100) if total_orders > 0 else 0)
    conversion = min(conversion, 100)
    
    # Refunds
    refunds = len(refunded_orders)
    
    # Unique customers (from successful orders)
    customer_emails = set()
    for o in successful_orders:
        if o.customer_email:
            customer_emails.add(o.customer_email)
    total_customers = len(customer_emails)
    # Repeat customers: approximation from multiple orders per email
    email_counts = {}
    for o in successful_orders:
        if o.customer_email:
            email_counts[o.customer_email] = email_counts.get(o.customer_email, 0) + 1
    repeat_customers = sum(1 for c in email_counts.values() if c > 1)
    
    return AnalyticsResponse(
        total_orders=total_orders,
        total_revenue=round(total_revenue, 2),
        average_order_value=round(avg_order, 2),
        payment_success_rate=round(success_rate, 1),
        total_products=total_products,
        low_stock_products=low_stock,
        total_items_sold=products_sold,
        profit=round(gross_profit, 2),
        margin=round(margin, 2),
        conversion_rate=round(conversion, 1),
        pending_orders=len(pending_orders),
        completed_orders=completed_count,
        cancelled_orders=len(cancelled_orders),
        refunds=refunds,
        total_customers=total_customers,
        repeat_customers=repeat_customers,
    )


@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard(db: AsyncSession = Depends(get_db)):
    """Full dashboard data for merchant overview with real data."""
    
    all_orders = await _get_all_orders(db)
    successful_orders = [o for o in all_orders if o.status == "success"]
    pending_orders = [o for o in all_orders if o.status in ("pending", "payment_initiated", "processing")]
    cancelled_orders_list = [o for o in all_orders if o.status == "cancelled"]
    
    total_revenue = await _calculate_revenue_from_orders(db, successful_orders)
    total_orders = len(all_orders)
    completed_count = len(successful_orders)
    avg_order = safe_float(total_revenue / completed_count if completed_count > 0 else 0)
    
    # Products from DB
    products_result = await db.execute(select(Product))
    products = products_result.scalars().all()
    products_map = {p.id: p for p in products}
    total_products = len(products)
    low_stock = len([p for p in products if 0 < p.stock <= 10])
    
    # Products sold from actual order data
    products_sold = await _calculate_products_sold_from_orders(db, successful_orders)
    
    # COGS from actual product cost * order quantities
    total_cogs = await _calculate_cogs_from_orders(db, successful_orders, products_map)
    gross_profit = safe_float(total_revenue - total_cogs)
    margin = safe_float((gross_profit / total_revenue * 100) if total_revenue > 0 else 0)
    
    # Conversion from real data
    conversion = safe_float((completed_count / total_orders * 100) if total_orders > 0 else 0)
    conversion = min(conversion, 100)
    
    # Revenue chart: last 30 days from successful orders
    now = datetime.now(timezone.utc)
    revenue_chart = []
    for i in range(30, -1, -1):
        day = (now - timedelta(days=i)).strftime("%b %d")
        day_start = (now - timedelta(days=i)).replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        day_orders = [
            o for o in successful_orders
            if o.created_at and _ensure_aware(o.created_at) and day_start <= _ensure_aware(o.created_at) <= day_end
        ]
        day_revenue = sum(safe_float(o.total, 0) for o in day_orders)
        revenue_chart.append(RevenueChartPoint(label=day, revenue=round(day_revenue, 2), orders=len(day_orders)))
    
    # Recent orders
    recent_orders = []
    for o in all_orders[:10]:
        recent_orders.append({
            "id": o.id[:8],
            "total": safe_float(o.total, 0),
            "status": o.status or "pending",
            "created_at": o.created_at.isoformat() if o.created_at else "",
        })
    
    # Top products by actual revenue from orders
    product_revenue_map = {}
    product_sales_map = {}
    for order in successful_orders:
        items = await _get_order_items_for_order(db, order.id)
        for item in items:
            pid = item.product_id
            product_revenue_map[pid] = product_revenue_map.get(pid, 0) + safe_float(item.subtotal, 0)
            product_sales_map[pid] = product_sales_map.get(pid, 0) + safe_int(item.quantity, 0)
    
    # Build top products from actual order data
    top_products_data = []
    sorted_pids = sorted(product_revenue_map.keys(), key=lambda p: product_revenue_map[p], reverse=True)[:5]
    for pid in sorted_pids:
        p = products_map.get(pid)
        top_products_data.append({
            "name": p.name if p else "Unknown",
            "revenue": round(product_revenue_map[pid], 2),
            "sales": product_sales_map.get(pid, 0),
            "stock": p.stock if p else 0,
        })
    
    # Notifications count
    notif_result = await db.execute(
        select(func.count(Notification.id)).where(Notification.is_read == False)
    )
    notif_count = notif_result.scalar() or 0
    
    # Unique customers
    customer_emails = set()
    for o in successful_orders:
        if o.customer_email:
            customer_emails.add(o.customer_email)
    
    # Best sellers - top 5 by quantity sold
    best_sellers = []
    for pid in sorted_pids[:5]:
        p = products_map.get(pid)
        if p:
            best_sellers.append({
                "name": p.name,
                "sales": product_sales_map.get(pid, 0),
                "revenue": round(product_revenue_map.get(pid, 0), 2),
                "category": p.category,
                "stock": p.stock,
            })
    
    # Slow movers - products with low sales relative to stock
    slow_movers = []
    for p in products:
        if p.stock > 0:
            sales_count = product_sales_map.get(p.id, 0)
            if sales_count < 3 and p.stock > 20:
                slow_movers.append({
                    "name": p.name,
                    "sales": sales_count,
                    "stock": p.stock,
                    "category": p.category,
                })
    slow_movers.sort(key=lambda x: x["sales"])
    slow_movers = slow_movers[:5]
    
    # Low stock list
    low_stock_list = []
    for p in products:
        if 0 < p.stock <= 10:
            low_stock_list.append({
                "name": p.name,
                "stock": p.stock,
                "category": p.category,
                "sales": product_sales_map.get(p.id, 0),
            })
    low_stock_list.sort(key=lambda x: x["stock"])
    
    # Category revenue
    cat_revenue = {}
    cat_sales = {}
    for order in successful_orders:
        items = await _get_order_items_for_order(db, order.id)
        for item in items:
            p = products_map.get(item.product_id)
            if p:
                cat = p.category
                cat_revenue[cat] = cat_revenue.get(cat, 0) + safe_float(item.subtotal, 0)
                cat_sales[cat] = cat_sales.get(cat, 0) + safe_int(item.quantity, 0)
    
    category_revenue = [
        {"category": cat, "revenue": round(rev, 2), "sales": cat_sales.get(cat, 0)}
        for cat, rev in sorted(cat_revenue.items(), key=lambda x: x[1], reverse=True)
    ]
    
    # Profit analytics
    profit_analytics = {
        "revenue": round(total_revenue, 2),
        "cogs": round(total_cogs, 2),
        "gross_profit": round(gross_profit, 2),
        "margin": round(margin, 2),
        "has_cost_data": any(p.cost_price and p.cost_price > 0 for p in products),
    }
    
    return DashboardResponse(
        total_revenue=round(total_revenue, 2),
        total_orders=total_orders,
        average_order_value=round(avg_order, 2),
        profit=round(gross_profit, 2),
        margin=round(margin, 2),
        products_sold=products_sold,
        low_stock_products=low_stock,
        conversion_rate=round(conversion, 1),
        revenue_chart=revenue_chart,
        recent_orders=recent_orders,
        top_products=top_products_data,
        notifications_count=notif_count,
        pending_orders=len(pending_orders),
        completed_orders=completed_count,
        cancelled_orders=len(cancelled_orders_list),
        total_customers=len(customer_emails),
        best_sellers=best_sellers,
        slow_movers=slow_movers,
        low_stock_list=low_stock_list,
        category_revenue=category_revenue,
        profit_analytics=profit_analytics,
    )


def _ensure_aware(dt: datetime) -> datetime:
    """Ensure datetime is timezone-aware (UTC)."""
    if dt and dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


@router.get("/revenue-chart")
async def revenue_chart(period: str = "30d", db: AsyncSession = Depends(get_db)):
    """Get revenue chart data for specified period from real order data."""
    now = datetime.now(timezone.utc)
    days_map = {"7d": 7, "30d": 30, "90d": 90, "1y": 365}
    days = days_map.get(period, 30)
    
    # Get successful orders
    orders_result = await db.execute(
        select(Order).where(Order.status == "success")
    )
    orders = orders_result.scalars().all()
    
    chart = []
    for i in range(days, -1, -1):
        day = (now - timedelta(days=i)).strftime("%b %d")
        day_start = (now - timedelta(days=i)).replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        day_orders = [
            o for o in orders
            if o.created_at and _ensure_aware(o.created_at) and day_start <= _ensure_aware(o.created_at) <= day_end
        ]
        day_revenue = sum(safe_float(o.total, 0) for o in day_orders)
        chart.append({"label": day, "revenue": round(day_revenue, 2), "orders": len(day_orders)})
    
    return chart
