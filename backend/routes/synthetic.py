"""
Synthetic Data API - generates realistic demo business data for analytics.
Clearly labeled as synthetic/demonstration data.
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Dict, Any
import random
import math
from datetime import datetime, timedelta, timezone

router = APIRouter()

# Fixed seed for reproducible, deterministic data. Each generator creates its
# OWN fresh Random(SEED) instance per call so the numbers never drift between
# requests or refreshes (a module-level RNG would advance on every call).
SEED = 42

CATEGORIES = ["Electronics", "Smartphones", "Laptops", "Accessories", "Audio", "Televisions", "Home Appliances", "Fashion", "Personal Care"]

PRODUCTS = [
    {"name": "Samsung Galaxy A55", "category": "Smartphones", "price": 28999, "cost": 18000, "rating": 4.3},
    {"name": "OnePlus Nord CE 4", "category": "Smartphones", "price": 24999, "cost": 15000, "rating": 4.2},
    {"name": "Apple iPhone 15", "category": "Smartphones", "price": 79900, "cost": 52000, "rating": 4.6},
    {"name": "Xiaomi Redmi Note 13 Pro", "category": "Smartphones", "price": 19999, "cost": 11000, "rating": 4.1},
    {"name": "Samsung Galaxy S24 Ultra", "category": "Smartphones", "price": 134999, "cost": 85000, "rating": 4.7},
    {"name": "HP Pavilion 15", "category": "Laptops", "price": 54999, "cost": 35000, "rating": 4.2},
    {"name": "Lenovo IdeaPad Slim 5", "category": "Laptops", "price": 49999, "cost": 30000, "rating": 4.1},
    {"name": "MacBook Air M3", "category": "Laptops", "price": 114900, "cost": 75000, "rating": 4.8},
    {"name": "ASUS ROG Strix G16", "category": "Laptops", "price": 109999, "cost": 72000, "rating": 4.4},
    {"name": "Sony WH-1000XM5", "category": "Audio", "price": 29990, "cost": 16000, "rating": 4.7},
    {"name": "JBL Tune 770NC", "category": "Audio", "price": 5999, "cost": 2800, "rating": 4.3},
    {"name": "boAt Rockerz 551", "category": "Audio", "price": 1799, "cost": 700, "rating": 4.0},
    {"name": "Apple AirPods Pro 2", "category": "Audio", "price": 24900, "cost": 14000, "rating": 4.6},
    {"name": "Samsung 55-inch 4K TV", "category": "Televisions", "price": 44999, "cost": 28000, "rating": 4.3},
    {"name": "LG 43-inch NanoCell TV", "category": "Televisions", "price": 34999, "cost": 21000, "rating": 4.2},
    {"name": "Logitech MX Master 3S", "category": "Accessories", "price": 8995, "cost": 4500, "rating": 4.6},
    {"name": "Samsung T7 1TB SSD", "category": "Accessories", "price": 10999, "cost": 6000, "rating": 4.5},
    {"name": "Portronics Car Mount", "category": "Accessories", "price": 599, "cost": 180, "rating": 3.9},
    {"name": "LG 7kg Washing Machine", "category": "Home Appliances", "price": 32999, "cost": 20000, "rating": 4.4},
    {"name": "Prestige Induction Cooktop", "category": "Home Appliances", "price": 2999, "cost": 1500, "rating": 4.1},
    {"name": "Men's Cotton T-Shirt", "category": "Fashion", "price": 799, "cost": 300, "rating": 4.0},
    {"name": "Nike Revolution 6", "category": "Fashion", "price": 3995, "cost": 1800, "rating": 4.3},
    {"name": "Dettol Liquid 200ml", "category": "Personal Care", "price": 89, "cost": 45, "rating": 4.4},
]


# Weight a product pick inversely to price so value items sell far more often
# than flagship electronics - keeps totals in a realistic SMB range.
_PRODUCT_WEIGHTS = [1.0 / (p["price"] ** 1.0) for p in PRODUCTS]


def _pick_product(rng: random.Random) -> dict:
    """Weighted product pick: cheaper/value items are chosen far more often."""
    return rng.choices(PRODUCTS, weights=_PRODUCT_WEIGHTS)[0]


def _generate_monthly_data(months: int = 12) -> List[Dict[str, Any]]:
    """Generate realistic monthly sales data for the last N months (deterministic)."""
    rng = random.Random(SEED)
    now = datetime.now(timezone.utc)
    monthly = []
    
    for i in range(months, 0, -1):
        month_date = now - timedelta(days=i * 30)
        month_name = month_date.strftime("%b %Y")
        
        # Seasonal factors (festival season Oct-Dec gets boost)
        month_num = month_date.month
        seasonal_factor = 1.0
        if month_num in (10, 11, 12):  # Festival season
            seasonal_factor = 1.35
        elif month_num in (1, 2):  # Post-festival dip
            seasonal_factor = 0.8
        elif month_num in (3, 4):  # Summer
            seasonal_factor = 1.1
        
        # Growth trend (slight upward)
        growth_factor = 1.0 + (months - i) * 0.015
        
        # Generate daily data for this month
        days_in_month = 30
        month_revenue = 0
        month_orders = 0
        month_units = 0
        month_cogs = 0
        
        for day in range(days_in_month):
            day_date = month_date + timedelta(days=day)
            day_of_week = day_date.weekday()
            
            # Weekend boost
            weekend_factor = 1.3 if day_of_week >= 5 else 1.0
            
            # Daily orders (~6-18 per day, with variance) - tuned so the
            # latest months land near the dashboard's ~₹6L/month scale.
            daily_orders = int(rng.gauss(10, 4) * seasonal_factor * growth_factor * weekend_factor)
            daily_orders = max(4, min(30, daily_orders))
            
            for _ in range(daily_orders):
                # Pick a product with value-weighted probability
                product = _pick_product(rng)
                
                qty = rng.choices([1, 2, 3], weights=[70, 20, 10])[0]
                price = product["price"] * rng.uniform(0.95, 1.0)  # Occasional discounts
                cost = product["cost"]
                
                month_revenue += price * qty
                month_cogs += cost * qty
                month_units += qty
                month_orders += 1
        
        profit = month_revenue - month_cogs
        margin = (profit / month_revenue * 100) if month_revenue > 0 else 0
        
        monthly.append({
            "month": month_name,
            "revenue": round(month_revenue, 2),
            "cogs": round(month_cogs, 2),
            "profit": round(profit, 2),
            "margin": round(margin, 1),
            "orders": month_orders,
            "units_sold": month_units,
            "avg_order_value": round(month_revenue / month_orders, 2) if month_orders > 0 else 0,
        })
    
    return monthly


def _generate_category_performance() -> List[Dict[str, Any]]:
    """Generate category performance data (deterministic)."""
    rng = random.Random(SEED)
    cat_data = {}
    for p in PRODUCTS:
        cat = p["category"]
        if cat not in cat_data:
            cat_data[cat] = {"revenue": 0, "units": 0, "products": 0, "avg_margin": 0}
        # Simulate sales
        sales = rng.randint(50, 500)
        cat_data[cat]["revenue"] += p["price"] * sales
        cat_data[cat]["units"] += sales
        cat_data[cat]["products"] += 1
        margin = ((p["price"] - p["cost"]) / p["price"] * 100) if p["price"] > 0 else 0
        cat_data[cat]["avg_margin"] += margin
    
    result = []
    for cat, data in cat_data.items():
        data["avg_margin"] = round(data["avg_margin"] / data["products"], 1) if data["products"] > 0 else 0
        result.append({
            "category": cat,
            "revenue": round(data["revenue"], 2),
            "units_sold": data["units"],
            "product_count": data["products"],
            "avg_margin": data["avg_margin"],
        })
    
    result.sort(key=lambda x: x["revenue"], reverse=True)
    return result


def _generate_growth_score(monthly_data: List[Dict]) -> Dict[str, Any]:
    """Calculate AI Growth Score from 0-100 based on business indicators."""
    if len(monthly_data) < 3:
        return {"score": 50, "factors": [], "summary": "Not enough historical data to calculate growth score."}
    
    recent_3 = monthly_data[-3:]
    earlier_3 = monthly_data[-6:-3] if len(monthly_data) >= 6 else monthly_data[:3]
    
    # Revenue growth
    recent_rev = sum(m["revenue"] for m in recent_3)
    earlier_rev = sum(m["revenue"] for m in earlier_3)
    rev_growth = ((recent_rev - earlier_rev) / earlier_rev * 100) if earlier_rev > 0 else 0
    
    # Profit margin trend
    recent_margin = sum(m["margin"] for m in recent_3) / 3
    earlier_margin = sum(m["margin"] for m in earlier_3) / 3
    margin_change = recent_margin - earlier_margin
    
    # Order growth
    recent_orders = sum(m["orders"] for m in recent_3)
    earlier_orders = sum(m["orders"] for m in earlier_3)
    order_growth = ((recent_orders - earlier_orders) / earlier_orders * 100) if earlier_orders > 0 else 0
    
    # AOV trend
    recent_aov = sum(m["avg_order_value"] for m in recent_3) / 3
    earlier_aov = sum(m["avg_order_value"] for m in earlier_3) / 3
    aov_change = ((recent_aov - earlier_aov) / earlier_aov * 100) if earlier_aov > 0 else 0
    
    # Score calculation (0-100)
    score = 50  # Base
    factors = []
    
    # Revenue growth (up to +20 points)
    if rev_growth > 20:
        score += 20
        factors.append({"name": "Revenue Growth", "impact": "positive", "value": f"+{rev_growth:.1f}%", "weight": 20})
    elif rev_growth > 5:
        score += 10
        factors.append({"name": "Revenue Growth", "impact": "positive", "value": f"+{rev_growth:.1f}%", "weight": 10})
    elif rev_growth > -5:
        factors.append({"name": "Revenue Growth", "impact": "neutral", "value": f"{rev_growth:.1f}%", "weight": 0})
    else:
        score -= 10
        factors.append({"name": "Revenue Growth", "impact": "negative", "value": f"{rev_growth:.1f}%", "weight": -10})
    
    # Profit margin (up to +15 points)
    if recent_margin > 35:
        score += 15
        factors.append({"name": "Profit Margin", "impact": "positive", "value": f"{recent_margin:.1f}%", "weight": 15})
    elif recent_margin > 25:
        score += 8
        factors.append({"name": "Profit Margin", "impact": "positive", "value": f"{recent_margin:.1f}%", "weight": 8})
    elif recent_margin > 15:
        factors.append({"name": "Profit Margin", "impact": "neutral", "value": f"{recent_margin:.1f}%", "weight": 0})
    else:
        score -= 5
        factors.append({"name": "Profit Margin", "impact": "negative", "value": f"{recent_margin:.1f}%", "weight": -5})
    
    # Order velocity (up to +15 points)
    if order_growth > 15:
        score += 15
        factors.append({"name": "Order Velocity", "impact": "positive", "value": f"+{order_growth:.1f}%", "weight": 15})
    elif order_growth > 5:
        score += 8
        factors.append({"name": "Order Velocity", "impact": "positive", "value": f"+{order_growth:.1f}%", "weight": 8})
    elif order_growth > -5:
        factors.append({"name": "Order Velocity", "impact": "neutral", "value": f"{order_growth:.1f}%", "weight": 0})
    else:
        score -= 5
        factors.append({"name": "Order Velocity", "impact": "negative", "value": f"{order_growth:.1f}%", "weight": -5})
    
    # AOV improvement (up to +10 points)
    if aov_change > 10:
        score += 10
        factors.append({"name": "Avg Order Value", "impact": "positive", "value": f"+{aov_change:.1f}%", "weight": 10})
    elif aov_change > 0:
        score += 5
        factors.append({"name": "Avg Order Value", "impact": "positive", "value": f"+{aov_change:.1f}%", "weight": 5})
    elif aov_change > -5:
        factors.append({"name": "Avg Order Value", "impact": "neutral", "value": f"{aov_change:.1f}%", "weight": 0})
    else:
        score -= 5
        factors.append({"name": "Avg Order Value", "impact": "negative", "value": f"{aov_change:.1f}%", "weight": -5})
    
    # Margin improvement (up to +10 points)
    if margin_change > 5:
        score += 10
        factors.append({"name": "Margin Trend", "impact": "positive", "value": f"+{margin_change:.1f}pp", "weight": 10})
    elif margin_change > 0:
        score += 5
        factors.append({"name": "Margin Trend", "impact": "positive", "value": f"+{margin_change:.1f}pp", "weight": 5})
    elif margin_change > -3:
        factors.append({"name": "Margin Trend", "impact": "neutral", "value": f"{margin_change:.1f}pp", "weight": 0})
    else:
        score -= 5
        factors.append({"name": "Margin Trend", "impact": "negative", "value": f"{margin_change:.1f}pp", "weight": -5})
    
    score = max(0, min(100, score))
    
    return {
        "score": score,
        "factors": factors,
        "summary": _growth_summary(score, factors),
    }


def _growth_summary(score: int, factors: List[Dict]) -> str:
    """Generate a human-readable growth summary."""
    if score >= 80:
        return "Your business is showing strong growth across multiple metrics. Keep up the great work!"
    elif score >= 60:
        return "Your business is growing well. Focus on areas where you see neutral or negative impacts to accelerate further."
    elif score >= 40:
        return "Your business has room for improvement. Consider focusing on the areas flagged below to boost growth."
    else:
        return "Your business metrics suggest some challenges. Review the factors below and consider strategic changes."


def _generate_investment_recommendations(monthly_data: List[Dict], cat_performance: List[Dict]) -> List[Dict[str, Any]]:
    """Generate AI investment recommendations based on synthetic data."""
    recommendations = []
    
    # Analyze category trends
    for cat in cat_performance[:3]:
        if cat["avg_margin"] > 35:
            recommendations.append({
                "type": "invest_more",
                "icon": "💰",
                "title": f"INVEST MORE: {cat['category']}",
                "category": cat["category"],
                "reason": f"Strong margins ({cat['avg_margin']}%) and consistent demand.",
                "expected_impact": f"Potential revenue growth through higher inventory availability.",
                "confidence": "High",
                "data": {"revenue": cat["revenue"], "margin": cat["avg_margin"], "units": cat["units_sold"]},
            })
    
    # Slow-moving categories
    if len(cat_performance) > 3:
        slow_cat = cat_performance[-1]
        recommendations.append({
            "type": "reduce",
            "icon": "📉",
            "title": f"REDUCE: {slow_cat['category']}",
            "category": slow_cat["category"],
            "reason": f"Lower revenue relative to other categories. Consider reducing inventory investment.",
            "expected_impact": "Free up capital for higher-performing categories.",
            "confidence": "Medium",
            "data": {"revenue": slow_cat["revenue"], "margin": slow_cat["avg_margin"]},
        })
    
    # Cross-sell opportunity
    recommendations.append({
        "type": "cross_sell",
        "icon": "🛒",
        "title": "CROSS-SELL: Accessories with Smartphones",
        "category": "Accessories",
        "reason": "Accessories have strong margins and pair naturally with smartphone purchases.",
        "expected_impact": "Estimated 15-25% increase in average order value.",
        "confidence": "High",
        "data": {"category": "Accessories", "margin": 55.0},
    })
    
    # Marketing opportunity
    recommendations.append({
        "type": "marketing",
        "icon": "📢",
        "title": "MARKETING: Promote High-Margin Audio Products",
        "category": "Audio",
        "reason": "Audio products show strong margins and growing demand.",
        "expected_impact": "Potential to increase audio category revenue by 20-30%.",
        "confidence": "Medium",
        "data": {"category": "Audio", "margin": 50.0},
    })
    
    return recommendations


def _generate_growth_opportunities(monthly_data: List[Dict], cat_performance: List[Dict]) -> List[Dict[str, Any]]:
    """Generate growth opportunity cards."""
    opportunities = []
    
    # Best performing category
    if cat_performance:
        best = cat_performance[0]
        opportunities.append({
            "type": "growth",
            "icon": "🚀",
            "title": "Growth Opportunity",
            "message": f"{best['category']} is your top-performing category with ₹{best['revenue']:,.0f} revenue. Consider expanding this line.",
            "category": best["category"],
            "metric": f"₹{best['revenue']:,.0f}",
        })
    
    # High margin
    for cat in cat_performance:
        if cat["avg_margin"] > 40:
            opportunities.append({
                "type": "high_margin",
                "icon": "💰",
                "title": "High Margin",
                "message": f"{cat['category']} products average {cat['avg_margin']}% margin. Prioritize marketing here.",
                "category": cat["category"],
                "metric": f"{cat['avg_margin']}%",
            })
            break
    
    # Rising demand (check recent months trend)
    if len(monthly_data) >= 2:
        recent = monthly_data[-1]
        prev = monthly_data[-2]
        if recent["orders"] > prev["orders"]:
            growth = ((recent["orders"] - prev["orders"]) / prev["orders"] * 100)
            opportunities.append({
                "type": "rising",
                "icon": "📈",
                "title": "Rising Demand",
                "message": f"Orders increased {growth:.0f}% last month. Prepare inventory for continued growth.",
                "metric": f"+{growth:.0f}%",
            })
    
    # Inventory risk
    opportunities.append({
        "type": "inventory_risk",
        "icon": "⚠️",
        "title": "Inventory Risk",
        "message": "Monitor slow-moving products to avoid overstocking. Consider promotions for items with low turnover.",
        "metric": "Monitor",
    })
    
    # Cross-sell
    opportunities.append({
        "type": "cross_sell",
        "icon": "🛒",
        "title": "Cross-Sell Opportunity",
        "message": "Bundle accessories with smartphone purchases to increase average order value.",
        "metric": "+15-25% AOV",
    })
    
    return opportunities


@router.get("/synthetic/dashboard")
async def get_synthetic_dashboard():
    """Get synthetic demo analytics data for the dashboard."""
    monthly_data = _generate_monthly_data(12)
    cat_performance = _generate_category_performance()
    growth_score = _generate_growth_score(monthly_data)
    recommendations = _generate_investment_recommendations(monthly_data, cat_performance)
    opportunities = _generate_growth_opportunities(monthly_data, cat_performance)
    
    # Calculate totals
    total_revenue = sum(m["revenue"] for m in monthly_data)
    total_profit = sum(m["profit"] for m in monthly_data)
    total_orders = sum(m["orders"] for m in monthly_data)
    total_units = sum(m["units_sold"] for m in monthly_data)
    avg_margin = sum(m["margin"] for m in monthly_data) / len(monthly_data)
    avg_aov = total_revenue / total_orders if total_orders > 0 else 0
    
    # Latest month vs previous
    latest = monthly_data[-1]
    previous = monthly_data[-2] if len(monthly_data) >= 2 else monthly_data[-1]
    revenue_growth = ((latest["revenue"] - previous["revenue"]) / previous["revenue"] * 100) if previous["revenue"] > 0 else 0
    profit_growth = ((latest["profit"] - previous["profit"]) / abs(previous["profit"]) * 100) if previous["profit"] != 0 else 0
    
    # What's going well
    whats_going_well = []
    if revenue_growth > 0:
        whats_going_well.append(f"Revenue grew {revenue_growth:.1f}% compared to last month.")
    if avg_margin > 30:
        whats_going_well.append(f"Healthy profit margins averaging {avg_margin:.0f}%.")
    if latest["orders"] > previous["orders"]:
        whats_going_well.append("Order volume is increasing month over month.")
    whats_going_well.append(f"Strong product catalog with {len(PRODUCTS)} products across {len(CATEGORIES)} categories.")
    
    # Recommended actions
    recommended_actions = [
        {"action": "Promote high-margin audio products", "category": "Audio", "reason": "Strong margins and growing demand"},
        {"action": "Bundle smartphone accessories", "category": "Accessories", "reason": "Increase average order value"},
        {"action": "Expand smartphone inventory", "category": "Smartphones", "reason": "Top-selling category with room to grow"},
        {"action": "Review slow-moving inventory", "category": "Home Appliances", "reason": "Optimize stock levels"},
        {"action": "Run promotion on fashion items", "category": "Fashion", "reason": "Boost seasonal sales"},
    ]
    
    # Investment allocation
    investment_allocation = {
        "total_budget": 100000,
        "label": "Suggested Allocation",
        "disclaimer": "Based on synthetic historical data — not actual investment advice",
        "allocations": [
            {"category": "Smartphone Inventory", "amount": 35000, "percentage": 35, "reason": "Highest revenue category"},
            {"category": "Accessories & Audio", "amount": 25000, "percentage": 25, "reason": "High margin cross-sell potential"},
            {"category": "Marketing & Promotions", "amount": 20000, "percentage": 20, "reason": "Drive demand across categories"},
            {"category": "Restocking Fast Movers", "amount": 12000, "percentage": 12, "reason": "Prevent stockouts on popular items"},
            {"category": "Experimentation", "amount": 8000, "percentage": 8, "reason": "Test new products and categories"},
        ],
    }
    
    return {
        "source": "synthetic",
        "label": "Demo Analytics — Synthetic Data",
        "disclaimer": "This data is generated for demonstration purposes. It does not represent actual business performance.",
        "summary": {
            "total_revenue": round(total_revenue, 2),
            "total_profit": round(total_profit, 2),
            "total_orders": total_orders,
            "total_units_sold": total_units,
            "avg_margin": round(avg_margin, 1),
            "avg_order_value": round(avg_aov, 2),
            "revenue_growth": round(revenue_growth, 1),
            "profit_growth": round(profit_growth, 1),
        },
        "monthly_data": monthly_data,
        "category_performance": cat_performance,
        "growth_score": growth_score,
        "investment_recommendations": recommendations,
        "growth_opportunities": opportunities,
        "whats_going_well": whats_going_well,
        "recommended_actions": recommended_actions,
        "investment_allocation": investment_allocation,
    }


@router.get("/synthetic/monthly")
async def get_synthetic_monthly():
    """Get monthly trend data."""
    return _generate_monthly_data(12)


@router.get("/synthetic/categories")
async def get_synthetic_categories():
    """Get category performance data."""
    return _generate_category_performance()
