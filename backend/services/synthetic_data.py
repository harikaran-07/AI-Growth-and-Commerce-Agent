"""
Synthetic Demo Data Service
===========================
Generates a deterministic, realistic 90-day merchant dataset for the
dashboard, growth analysis, charts, and recommendations.

- Uses a FIXED random seed re-created on every call, so the numbers are
  identical on every request / refresh (no flicker between page loads).
- Derives product performance from the REAL catalog (stable product ids,
  names, prices, cost prices, images) so every recommendation points at a
  real, orderable product.
- Labeled everywhere as synthetic demo data. It never touches real orders,
  payments, or Razorpay — real payment records stay completely separate.
"""

import hashlib
import logging
import random
from datetime import datetime, timedelta, timezone
from typing import Dict, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models.models import Product

logger = logging.getLogger(__name__)

SEED = 42
DAYS = 90

# ── Tunable business-model parameters (kept central for calibration) ──
BASE_ORDERS_PER_DAY = 14.0      # mean daily orders
ORDER_VOLATILITY = 4.5          # daily stddev
ITEM_WEIGHTS = [45, 35, 15, 5]  # qty 1/2/3/4
VALUE_PRICE_CAP = 900           # cheap pool (accessories, cases, cables, fashion)
MID_PRICE_CAP = 15000           # mid pool (mid-range electronics)
# Share of item picks by pool: [value, mid, flagship]
POOL_WEIGHTS = [99.4, 0.55, 0.05]
DISCOUNT_PROB = 0.12            # share of orders with a discount
DISCOUNT_RANGE = (0.05, 0.12)
REFUND_PROB = 0.02              # share of orders refunded
SESSION_PER_ORDER = 14.0        # visitors per completed order (funnel base)
RETURNING_POOL = 300            # deterministic base of repeat customers


def _product_weight(p) -> float:
    """Deterministic popularity weight from the product's stable id + rating."""
    h = int(hashlib.md5(p.id.encode()).hexdigest()[:8], 16)
    rating = (p.rating or 4.0)
    return max(0.2, 1.0 + (h % 100) / 50.0 + (rating - 3.5) * 0.8)


def _pool_of(p) -> int:
    price = float(p.price or 0)
    if price <= VALUE_PRICE_CAP:
        return 0
    if price <= MID_PRICE_CAP:
        return 1
    return 2


async def _load_products(db: AsyncSession) -> List:
    result = await db.execute(select(Product).where(Product.is_active == True))  # noqa: E712
    products = result.scalars().all()
    return sorted(products, key=lambda p: p.id)  # stable order → stable determinism


async def generate_synthetic_dataset(db: AsyncSession) -> Dict:
    """Generate the full deterministic synthetic dashboard dataset."""
    rng = random.Random(SEED)  # fresh seed every call → identical output
    products = await _load_products(db)
    if not products:
        return _empty_dataset()

    weights = [_product_weight(p) for p in products]
    pools = [_pool_of(p) for p in products]
    pools_idx = {0: [], 1: [], 2: []}
    for i, pl in enumerate(pools):
        pools_idx[pl].append(i)

    now = datetime.now(timezone.utc)
    start = (now - timedelta(days=DAYS - 1)).replace(hour=0, minute=0, second=0, microsecond=0)

    daily_rows = []          # one dict per day
    order_rows = []          # one dict per synthetic order
    product_stats = {}       # product_id -> {units, revenue, cogs, orders, discounts}
    customer_stats = {}      # customer_key -> {orders, spend, first, last}
    cat_stats = {}           # category -> {units, revenue}

    for day_offset in range(DAYS):
        date = start + timedelta(days=day_offset)
        wd = date.weekday()
        weekend = 1.30 if wd >= 5 else 1.0
        month = date.month
        season = 1.35 if month in (10, 11, 12) else (0.8 if month in (1, 2) else (1.1 if month in (3, 4) else 1.0))
        growth = 1.0 + day_offset / DAYS * 0.12  # gentle upward trend over the window
        n_orders = max(4, int(round(rng.gauss(BASE_ORDERS_PER_DAY, ORDER_VOLATILITY) * weekend * season * growth)))

        day_revenue = 0.0
        day_cogs = 0.0
        day_units = 0
        day_discount = 0.0
        day_refund = 0.0
        day_refunds = 0
        day_orders = 0

        for _ in range(n_orders):
            qty = rng.choices([1, 2, 3, 4], weights=ITEM_WEIGHTS)[0]
            pool = rng.choices([0, 1, 2], weights=POOL_WEIGHTS)[0]
            candidates = pools_idx.get(pool) or [0]
            idx = rng.choices(candidates, weights=[weights[i] for i in candidates])[0]
            p = products[idx]

            discount = 0.0
            if rng.random() < DISCOUNT_PROB:
                discount = rng.uniform(*DISCOUNT_RANGE)
            unit_price = float(p.price or 0) * (1 - discount)
            cost = float(p.cost_price) if (p.cost_price or 0) > 0 else float(p.price or 0) * 0.55
            subtotal = unit_price * qty

            is_refunded = rng.random() < REFUND_PROB
            if is_refunded:
                day_refunds += 1
                day_refund += subtotal
            else:
                day_revenue += subtotal
                day_orders += 1

            day_cogs += cost * qty
            day_units += qty
            day_discount += (float(p.price or 0) - unit_price) * qty

            # product stats (include refunded orders in units so best-sellers stay meaningful)
            ps = product_stats.setdefault(p.id, {"units": 0, "revenue": 0.0, "cogs": 0.0, "orders": 0, "discounts": 0.0})
            ps["units"] += qty
            ps["cogs"] += cost * qty
            ps["discounts"] += (float(p.price or 0) - unit_price) * qty
            if not is_refunded:
                ps["revenue"] += subtotal
                ps["orders"] += 1

            # category stats
            cat = p.category or "Other"
            cs = cat_stats.setdefault(cat, {"units": 0, "revenue": 0.0})
            cs["units"] += qty
            if not is_refunded:
                cs["revenue"] += subtotal

            # customer: ~35% returning (deterministic pool), rest new
            if rng.random() < 0.35:
                cust_key = f"returning_{rng.randrange(RETURNING_POOL)}"
            else:
                cust_key = f"new_{day_offset}_{len(order_rows)}_{int(hashlib.md5(p.id.encode()).hexdigest()[:6], 16)}"
            cs_ = customer_stats.setdefault(cust_key, {"orders": 0, "spend": 0.0, "first": date, "last": date})
            cs_["orders"] += 1
            cs_["spend"] += subtotal if not is_refunded else 0
            cs_["last"] = date
            if cs_["orders"] == 1:
                cs_["first"] = date

            order_rows.append({
                "date": date, "qty": qty, "unit_price": unit_price, "cost": cost,
                "discount": discount, "refunded": is_refunded,
                "product_id": p.id, "name": p.name, "price": float(p.price or 0),
                "category": cat, "subcategory": p.subcategory or "", "image_url": p.image_url or "",
                "customer": cust_key,
            })

        daily_rows.append({
            "label": date.strftime("%b %d"),
            "date": date.isoformat(),
            "revenue": round(day_revenue, 2),
            "orders": day_orders,
            "units": day_units,
            "cogs": round(day_cogs, 2),
            "discounts": round(day_discount, 2),
            "refunds": round(day_refund, 2),
            "refund_count": day_refunds,
        })

    # ── Aggregates ──
    total_revenue = sum(d["revenue"] for d in daily_rows)
    total_orders = sum(d["orders"] for d in daily_rows)
    total_units = sum(d["units"] for d in daily_rows)
    total_cogs = sum(d["cogs"] for d in daily_rows)
    total_discounts = sum(d["discounts"] for d in daily_rows)
    total_refunds = sum(d["refunds"] for d in daily_rows)
    avg_order_value = total_revenue / total_orders if total_orders else 0
    gross_profit = total_revenue - total_cogs - total_discounts - total_refunds
    margin = (gross_profit / total_revenue * 100) if total_revenue > 0 else 0
    total_customers = len(customer_stats)
    total_sessions = int(total_orders * SESSION_PER_ORDER)
    conversion_rate = (total_orders / total_sessions * 100) if total_sessions else 0

    # ── Best sellers / top products / slow movers from real catalog + synthetic sales ──
    products_map = {p.id: p for p in products}
    ranked = sorted(product_stats.items(), key=lambda kv: kv[1]["revenue"], reverse=True)

    def _item(p, stats, with_image=False):
        prod = products_map.get(p)
        d = {
            "id": p if prod is None else prod.id,
            "name": prod.name if prod else p,
            "category": prod.category if prod else "Other",
            "price": float(prod.price or 0) if prod else 0,
            "units_sold": stats["units"],
            "sales": stats["orders"],
            "revenue": round(stats["revenue"], 2),
            "stock": prod.stock if prod else 0,
        }
        if with_image:
            d["image_url"] = (prod.image_url or "") if prod else ""
        return d

    top_products = [_item(pid, st, with_image=True) for pid, st in ranked[:8]]
    best_sellers = sorted(product_stats.items(), key=lambda kv: kv[1]["units"], reverse=True)[:6]
    best_sellers = [_item(pid, st, with_image=True) for pid, st in best_sellers]

    # slow movers: high stock, low synthetic sales
    sold_ids = set(product_stats.keys())
    slow = []
    for p in products:
        if (p.stock or 0) > 20 and p.id not in sold_ids:
            slow.append({"id": p.id, "name": p.name, "sales": 0, "stock": p.stock, "category": p.category or "Other", "image_url": p.image_url or ""})
    slow = sorted(slow, key=lambda x: x["stock"], reverse=True)[:5]

    # low stock list (real inventory status, joined with synthetic velocity)
    low = []
    for p in products:
        st = p.stock or 0
        if 0 < st <= 10:
            sold = product_stats.get(p.id, {}).get("units", 0)
            low.append({"id": p.id, "name": p.name, "stock": st, "category": p.category or "Other",
                        "sales": sold, "status": "Critical" if st <= 3 else "Low",
                        "image_url": p.image_url or ""})
    low.sort(key=lambda x: x["stock"])
    low_stock_count = len(low)

    # ── Category performance ──
    category_revenue = [
        {"category": cat, "revenue": round(st["revenue"], 2), "sales": st["units"]}
        for cat, st in sorted(cat_stats.items(), key=lambda kv: kv[1]["revenue"], reverse=True)
    ]

    # ── Customer analytics ──
    # Segments form a clean, mutually-exclusive partition of total customers:
    #   At Risk      → single order, last purchase older than 30 days
    #   High Value   → repeat buyers in the top spend tier (~top 20%)
    #   Returning    → other repeat buyers (2+ orders)
    #   New          → everyone else (recent first purchase)
    # Returning + High Value together = all repeat customers, so the
    # repeat_purchase_rate below is consistent with the visible counts.
    now_dt = datetime.now(timezone.utc)
    cutoff_30 = now_dt - timedelta(days=30)
    seg = {"At Risk": 0, "High Value": 0, "Returning": 0, "New": 0}

    # spend threshold at the ~80th percentile of repeat customers
    repeat_spends = sorted((c["spend"] for c in customer_stats.values() if c["orders"] >= 2), reverse=True)
    spend_cutoff = 0
    if repeat_spends:
        idx = min(int(len(repeat_spends) * 0.80), len(repeat_spends) - 1)
        spend_cutoff = repeat_spends[idx]

    for ck, c in customer_stats.items():
        if c["orders"] >= 2:
            if spend_cutoff > 0 and c["spend"] >= spend_cutoff:
                seg["High Value"] += 1
            else:
                seg["Returning"] += 1
        elif c["last"] < cutoff_30:
            seg["At Risk"] += 1
        else:
            seg["New"] += 1

    # Guarantee the partition sums exactly to the total (protect against edge
    # cases such as customers whose only order was refunded).
    diff = total_customers - sum(seg.values())
    if diff > 0:
        seg["New"] += diff
    elif diff < 0:
        seg["New"] = max(0, seg["New"] + diff)

    returning_customers = seg["Returning"] + seg["High Value"]
    repeat_purchase_rate = (returning_customers / total_customers * 100) if total_customers else 0
    avg_customer_value = total_revenue / total_customers if total_customers else 0

    customers = {
        "total": total_customers,
        "new": seg["New"],
        "returning": returning_customers,
        "repeat_purchase_rate": round(repeat_purchase_rate, 1),
        "avg_customer_value": round(avg_customer_value, 2),
        "segments": [
            {"name": seg_name, "count": seg[seg_name]}
            for seg_name in ("New", "Returning", "High Value", "At Risk")
        ],
    }

    # ── Conversion funnel (visitors → views → cart → checkout → orders) ──
    visitors = total_sessions
    product_views = int(visitors * 0.70)
    add_to_cart = int(visitors * 0.21)
    checkout_started = int(visitors * 0.12)
    funnel = [
        {"stage": "Visitors", "count": visitors, "pct": 100.0},
        {"stage": "Product Views", "count": product_views, "pct": round(product_views / visitors * 100, 1)},
        {"stage": "Add to Cart", "count": add_to_cart, "pct": round(add_to_cart / product_views * 100, 1)},
        {"stage": "Checkout Started", "count": checkout_started, "pct": round(checkout_started / add_to_cart * 100, 1)},
        {"stage": "Completed Orders", "count": total_orders, "pct": round(total_orders / checkout_started * 100, 1) if checkout_started else 0},
    ]

    # ── Growth insights (computed from the dataset) ──
    insights = []
    if category_revenue:
        top_cat = category_revenue[0]
        insights.append(f"📊 {top_cat['category']} generated the highest revenue (₹{top_cat['revenue']:,.0f}) over the last 90 days.")
    if best_sellers:
        bs = best_sellers[0]
        insights.append(f"🔥 {bs['name']} is the best seller with {bs['units_sold']} units sold.")
    # low stock risk on fast movers
    fast_movers_low = [x for x in low if x["sales"] > 0][:3]
    if fast_movers_low:
        names = ", ".join(" ".join(x["name"].split(" ")[:2]) for x in fast_movers_low[:2])
        insights.append(f"⚠️ High-selling products are approaching low stock ({names}).")
    # returning vs new AOV
    if customers["returning"] and customers["new"]:
        insights.append(f"👥 Returning customers ({customers['returning']}) place repeat orders, lifting repeat purchase rate to {customers['repeat_purchase_rate']:.0f}%.")
    # weekend vs weekday revenue
    weekend_rev = sum(d["revenue"] for d in daily_rows if datetime.fromisoformat(d["date"]).weekday() >= 5)
    weekday_rev = total_revenue - weekend_rev
    weekend_days = sum(1 for d in daily_rows if datetime.fromisoformat(d["date"]).weekday() >= 5)
    weekday_days = DAYS - weekend_days
    if weekday_days and weekend_days:
        wd_avg = weekend_rev / weekend_days
        wk_avg = weekday_rev / weekday_days
        if wd_avg > wk_avg:
            insights.append(f"📈 Weekend conversion is stronger: avg ₹{wd_avg:,.0f}/day vs ₹{wk_avg:,.0f}/day on weekdays.")
    # discount effectiveness
    if total_revenue > 0:
        discount_share = (total_discounts / (total_revenue + total_discounts) * 100)
        insights.append(f"🏷️ Discounts accounted for {discount_share:.1f}% of gross sales while keeping margin at {margin:.1f}%.")

    # ── Growth opportunities (actionable cards) ──
    opportunities = []
    if category_revenue and len(category_revenue) > 1:
        opportunities.append({
            "opportunity": "Increase Revenue",
            "impact": f"₹{top_cat['revenue'] * 0.10:,.0f} potential (10% uplift)",
            "reason": f"{top_cat['category']} leads revenue; cross-promote it with secondary categories.",
            "action": "Run a bundled promotion pairing top category items with high-margin accessories.",
        })
    opportunities.append({
        "opportunity": "Improve Conversion",
        "impact": f"+{round(conversion_rate * 0.5, 1)} pts conversion",
        "reason": f"Only {round(funnel[4]['pct'], 1)}% of checkout starts convert to orders.",
        "action": "Simplify checkout: reduce form fields and surface Razorpay UPI at first step.",
    })
    cart_drop = (checkout_started - total_orders) if checkout_started > total_orders else 0
    if cart_drop > 0:
        opportunities.append({
            "opportunity": "Recover Abandoned Carts",
            "impact": f"₹{avg_order_value * cart_drop:,.0f} recoverable",
            "reason": f"{cart_drop} carts reached checkout but were not completed.",
            "action": "Send a follow-up reminder with a small incentive for abandoned carts.",
        })
    opportunities.append({
        "opportunity": "Increase Average Order Value",
        "impact": f"+{round(avg_order_value * 0.15):,} per order",
        "reason": "Best sellers rarely include complementary accessories.",
        "action": "Recommend compatible accessories (cases, chargers, cables) on product pages.",
    })
    if low_stock_count > 0:
        opportunities.append({
            "opportunity": "Reduce Stockouts",
            "impact": "Protect ~5% of revenue",
            "reason": f"{low_stock_count} products are at low/critical stock levels.",
            "action": "Reorder top-selling low-stock items ahead of peak demand.",
        })

    return {
        "data_source": "synthetic",
        "label": "Synthetic Demo Data",
        "disclaimer": "Dashboard analytics are synthetic demo data. Real orders and Razorpay payments are recorded separately.",
        "total_revenue": round(total_revenue, 2),
        "total_orders": total_orders,
        "average_order_value": round(avg_order_value, 2),
        "profit": round(gross_profit, 2),
        "margin": round(margin, 2),
        "products_sold": total_units,
        "low_stock_products": low_stock_count,
        "conversion_rate": round(conversion_rate, 2),
        "completed_orders": total_orders,
        "pending_orders": 0,
        "cancelled_orders": 0,
        "total_customers": total_customers,
        "payment_success_rate": 96.5,
        "revenue_chart": [{"label": d["label"], "revenue": d["revenue"], "orders": d["orders"]} for d in daily_rows],
        "orders_chart": [{"label": d["label"], "orders": d["orders"]} for d in daily_rows],
        "profit_chart": [{"label": d["label"], "revenue": d["revenue"], "cogs": d["cogs"], "discounts": d["discounts"], "refunds": d["refunds"]} for d in daily_rows],
        "recent_orders": [
            {"id": f"ORD-{i:04d}", "total": round(o["unit_price"] * o["qty"], 2), "status": "success",
             "created_at": o["date"].isoformat(), "name": o["name"]}
            for i, o in enumerate(order_rows[-10:][::-1])
        ],
        "top_products": top_products,
        "best_sellers": best_sellers,
        "slow_movers": slow,
        "low_stock_list": low,
        "category_revenue": category_revenue,
        "profit_analytics": {
            "revenue": round(total_revenue, 2),
            "cogs": round(total_cogs, 2),
            "discounts": round(total_discounts, 2),
            "refunds": round(total_refunds, 2),
            "gross_profit": round(gross_profit, 2),
            "margin": round(margin, 2),
            "has_cost_data": True,
        },
        "customers": customers,
        "funnel": funnel,
        "growth_insights": insights,
        "growth_opportunities": opportunities,
        "notifications_count": 0,
        "total_products": len(products),
    }


def _empty_dataset() -> Dict:
    return {
        "data_source": "synthetic", "label": "Synthetic Demo Data",
        "total_revenue": 0, "total_orders": 0, "average_order_value": 0,
        "profit": 0, "margin": 0, "products_sold": 0, "low_stock_products": 0,
        "conversion_rate": 0, "completed_orders": 0, "pending_orders": 0,
        "cancelled_orders": 0, "total_customers": 0, "payment_success_rate": 0,
        "revenue_chart": [], "orders_chart": [], "profit_chart": [],
        "recent_orders": [], "top_products": [], "best_sellers": [],
        "slow_movers": [], "low_stock_list": [], "category_revenue": [],
        "profit_analytics": {"revenue": 0, "cogs": 0, "discounts": 0, "refunds": 0,
                             "gross_profit": 0, "margin": 0, "has_cost_data": False},
        "customers": {"total": 0, "new": 0, "returning": 0, "repeat_purchase_rate": 0,
                      "avg_customer_value": 0, "segments": []},
        "funnel": [], "growth_insights": [], "growth_opportunities": [],
        "notifications_count": 0, "total_products": 0,
    }
async def generate_chart(db: AsyncSession, period: str = "30d") -> List[Dict]:
    """Deterministic revenue/orders series for 7d/30d/90d/1y.

    7d/30d/90d are exact tail slices of the same 90-day series that powers the
    dashboard KPIs, so chart totals always agree with the summary cards.
    1y is its own deterministic 365-day series (same seasonal/weekend model).
    """
    days_map = {"7d": 7, "30d": 30, "90d": 90, "1y": 365}
    days = days_map.get(period, 30)
    if days == 365:
        return await _generate_long_series(db, 365)
    ds = await generate_synthetic_dataset(db)
    rc = ds.get("revenue_chart") or []
    return rc[-days:] if len(rc) > days else rc


async def _generate_long_series(db: AsyncSession, days: int) -> List[Dict]:
    """Deterministic daily series for a full year (used by the 1y view)."""
    rng = random.Random(SEED)
    products = await _load_products(db)
    if not products:
        return []
    weights = [_product_weight(p) for p in products]
    pools = [_pool_of(p) for p in products]
    pools_idx = {0: [], 1: [], 2: []}
    for i, pl in enumerate(pools):
        pools_idx[pl].append(i)

    now = datetime.now(timezone.utc)
    start = (now - timedelta(days=days - 1)).replace(hour=0, minute=0, second=0, microsecond=0)
    series = []
    for day_offset in range(days):
        date = start + timedelta(days=day_offset)
        wd = date.weekday()
        weekend = 1.30 if wd >= 5 else 1.0
        month = date.month
        season = 1.35 if month in (10, 11, 12) else (0.8 if month in (1, 2) else (1.1 if month in (3, 4) else 1.0))
        growth = 1.0 + day_offset / max(days, 1) * 0.25
        n = max(4, int(round(rng.gauss(BASE_ORDERS_PER_DAY, ORDER_VOLATILITY) * weekend * season * growth)))
        revenue = 0.0
        for _ in range(n):
            pool = rng.choices([0, 1, 2], weights=POOL_WEIGHTS)[0]
            candidates = pools_idx.get(pool) or [0]
            idx = rng.choices(candidates, weights=[weights[i] for i in candidates])[0]
            qty = rng.choices([1, 2, 3, 4], weights=ITEM_WEIGHTS)[0]
            price = float(products[idx].price or 0)
            if rng.random() < DISCOUNT_PROB:
                price *= (1 - rng.uniform(*DISCOUNT_RANGE))
            revenue += price * qty
        series.append({"label": date.strftime("%b %d"), "revenue": round(revenue, 2), "orders": n})
    return series
