"""
Analytics API - dashboard stats, revenue charts, merchant overview.

- GET /api/analytics/          → REAL summary from actual orders/payments.
- GET /api/analytics/dashboard → merchant dashboard demo dataset (Synthetic
  Demo Data, clearly labeled) generated deterministically from the real
  catalog. Real orders/Razorpay payments remain separate.
- GET /api/analytics/revenue-chart?period=7d|30d|90d|1y → synthetic series.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from models.database import get_db
from models.models import Order, Payment, AuditLog, CartItem, Product, Notification, OrderItem
from services.synthetic_data import generate_synthetic_dataset, generate_chart
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


@router.get("/dashboard")
async def get_dashboard(db: AsyncSession = Depends(get_db)):
    """Full merchant dashboard data.

    Serves the deterministic Synthetic Demo Data dataset (clearly labeled via
    `data_source` / `label` / `disclaimer`) so a new merchant dashboard never
    looks empty. Real orders and Razorpay payments stay separate - they are
    reported by /api/analytics/ and the Orders/Payments pages.
    """
    return await generate_synthetic_dataset(db)


def _ensure_aware(dt: datetime) -> datetime:
    """Ensure datetime is timezone-aware (UTC)."""
    if dt and dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


@router.get("/revenue-chart")
async def revenue_chart(period: str = "30d", db: AsyncSession = Depends(get_db)):
    """Revenue/orders series for 7d/30d/90d/1y (synthetic demo, deterministic)."""
    return await generate_chart(db, period)
