"""
AI Pricing Engine - recommends optimal pricing based on product data.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.database import get_db
from models.models import Product, AuditLog
from pydantic import BaseModel
from typing import Optional
import logging
import random

logger = logging.getLogger(__name__)
router = APIRouter()


class PricingRecommendation(BaseModel):
    product_id: str
    product_name: str
    current_price: float
    cost_price: Optional[float]
    recommended_price: float
    expected_revenue_impact: float
    expected_margin_impact: float
    expected_conversion_impact: float
    confidence: float
    explanation: str
    direction: str  # "increase", "decrease", "maintain"


class PriceApplyRequest(BaseModel):
    product_id: str
    new_price: float


def calculate_pricing_recommendation(product: Product) -> PricingRecommendation:
    """Calculate AI pricing recommendation based on product metrics."""
    current_price = product.price
    cost_price = product.cost_price or (current_price * 0.6)
    stock = product.stock
    sales = product.sales or 0
    rating = product.rating or 4.0

    # Determine demand signal
    demand_score = 0
    if sales > 50:
        demand_score = 3  # High demand
    elif sales > 20:
        demand_score = 2  # Medium demand
    elif sales > 5:
        demand_score = 1  # Low demand
    else:
        demand_score = 0  # Very low demand

    # Stock pressure
    stock_pressure = 0
    if stock > 50:
        stock_pressure = 2  # Overstocked
    elif stock > 20:
        stock_pressure = 1  # Well stocked
    elif stock <= 5:
        stock_pressure = -1  # Low stock
    else:
        stock_pressure = 0  # Normal

    current_margin = ((current_price - cost_price) / current_price * 100) if current_price > 0 else 0

    # Calculate recommendation
    price_change_pct = 0
    explanation_parts = []

    # High demand + low stock = can increase price
    if demand_score >= 2 and stock_pressure <= 0:
        price_change_pct = random.uniform(3, 8)
        explanation_parts.append("High demand with limited stock supports a price increase")
    # Low demand = decrease to stimulate sales
    elif demand_score <= 1 and stock_pressure >= 1:
        price_change_pct = random.uniform(-10, -3)
        explanation_parts.append("Lowering price to stimulate demand for slow-moving inventory")
    # High stock = slight decrease
    elif stock_pressure >= 2:
        price_change_pct = random.uniform(-8, -2)
        explanation_parts.append("Overstocked product - price reduction recommended to clear inventory")
    # Good rating + moderate sales = slight increase
    elif rating >= 4.0 and demand_score >= 1:
        price_change_pct = random.uniform(1, 5)
        explanation_parts.append("Strong ratings justify a modest price increase")
    # Default: maintain or small adjustment
    else:
        price_change_pct = random.uniform(-2, 2)
        explanation_parts.append("Current pricing appears aligned with market conditions")

    # Ensure margin stays above 5%
    recommended_price = round(current_price * (1 + price_change_pct / 100), 0)
    new_margin = ((recommended_price - cost_price) / recommended_price * 100) if recommended_price > 0 else 0

    if new_margin < 5 and recommended_price < current_price:
        recommended_price = round(cost_price / 0.9, 0)  # Ensure 10% margin minimum
        explanation_parts.append("Price adjusted to maintain minimum margin threshold")

    recommended_price = max(recommended_price, cost_price * 1.05)  # Never below 5% margin

    direction = "increase" if recommended_price > current_price else ("decrease" if recommended_price < current_price else "maintain")

    # Impact estimates
    revenue_impact = round((recommended_price - current_price) * sales, 2)
    margin_impact = round(new_margin - current_margin, 2)
    conversion_impact = round(-price_change_pct * 0.5, 1)  # Rough estimate: -0.5% conversion per 1% price increase

    confidence = random.uniform(0.65, 0.92)

    return PricingRecommendation(
        product_id=product.id,
        product_name=product.name,
        current_price=current_price,
        cost_price=cost_price,
        recommended_price=recommended_price,
        expected_revenue_impact=revenue_impact,
        expected_margin_impact=margin_impact,
        expected_conversion_impact=conversion_impact,
        confidence=round(confidence, 2),
        explanation="; ".join(explanation_parts),
        direction=direction,
    )


@router.get("/recommend/{product_id}", response_model=PricingRecommendation)
async def get_pricing_recommendation(product_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return calculate_pricing_recommendation(product)


@router.post("/apply", response_model=dict)
async def apply_price(request: PriceApplyRequest, db: AsyncSession = Depends(get_db)):
    """Apply a new price to a product."""
    result = await db.execute(select(Product).where(Product.id == request.product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    old_price = product.price
    product.previous_price = old_price
    product.price = request.new_price

    if product.cost_price and product.cost_price > 0:
        product.margin = round(((request.new_price - product.cost_price) / request.new_price) * 100, 2) if request.new_price > 0 else 0

    # Create audit event
    audit = AuditLog(
        action="PRICE_CHANGED",
        description=f"Price changed from ₹{old_price} to ₹{request.new_price} for {product.name}",
        event_type="pricing",
        related_entity=product.id,
        financial_impact=request.new_price - old_price,
        final_status="success",
    )
    db.add(audit)

    # Create notification
    from models.models import Notification
    notif = Notification(
        title="Price Updated",
        message=f"{product.name}: ₹{old_price} → ₹{request.new_price}",
        type="success",
        related_entity=product.id,
    )
    db.add(notif)

    await db.commit()
    return {"status": "success", "old_price": old_price, "new_price": request.new_price}


@router.get("/batch/{category}", response_model=list)
async def get_pricing_recommendations_by_category(category: str, limit: int = 20, db: AsyncSession = Depends(get_db)):
    """Get pricing recommendations for a category."""
    result = await db.execute(
        select(Product).where(Product.category == category, Product.is_active == True).limit(limit)
    )
    products = result.scalars().all()
    return [calculate_pricing_recommendation(p) for p in products]
