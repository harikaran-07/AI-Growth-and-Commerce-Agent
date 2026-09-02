"""
Agent Tools - Safe backend tools that the LLM can call.
The LLM REQUESTS a tool call, but the backend executes it.
The LLM never directly accesses the database or credentials.
"""

import json
import uuid
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from models.models import (
    Product, ProductRelationship, Cart, CartItem,
    Order, OrderItem, Policy, Approval, AuditLog, Customer
)

logger = logging.getLogger(__name__)

# In-memory session store for conversation context
session_store: Dict[str, Dict[str, Any]] = {}


def get_session_data(session_id: str) -> Dict[str, Any]:
    """Get or create session data."""
    if session_id not in session_store:
        session_store[session_id] = {
            "last_search_results": [],
            "cart_id": None,
            "last_order_id": None,
            "last_approval_id": None,
        }
    return session_store[session_id]


async def log_audit_event(
    db: AsyncSession,
    session_id: str,
    action: str,
    tool_called: str = None,
    input_data: str = None,
    decision: str = None,
    policy_result: str = None,
    approval_status: str = None,
    payment_reference: str = None,
    final_status: str = None,
):
    """Record an audit log entry."""
    audit = AuditLog(
        session_id=session_id,
        user="buyer",
        action=action,
        tool_called=tool_called,
        input_data=input_data[:500] if input_data else None,
        decision=decision,
        policy_result=policy_result,
        approval_status=approval_status,
        payment_reference=payment_reference,
        final_status=final_status,
        created_at=datetime.now(timezone.utc)
    )
    db.add(audit)
    await db.commit()


async def execute_tool(
    tool_name: str,
    arguments: Dict[str, Any],
    db: AsyncSession,
    session_id: str
) -> str:
    """Execute a tool and return the result as a JSON string."""
    session_data = get_session_data(session_id)

    try:
        if tool_name == "search_products":
            return await _search_products(arguments, db, session_id, session_data)
        elif tool_name == "get_product_details":
            return await _get_product_details(arguments, db)
        elif tool_name == "check_inventory":
            return await _check_inventory(arguments, db)
        elif tool_name == "recommend_upsell":
            return await _recommend_upsell(arguments, db)
        elif tool_name == "recommend_cross_sell":
            return await _recommend_cross_sell(arguments, db)
        elif tool_name == "add_to_cart":
            return await _add_to_cart(arguments, db, session_id, session_data)
        elif tool_name == "get_cart":
            return await _get_cart(db, session_id, session_data)
        elif tool_name == "calculate_cart_total":
            return await _calculate_cart_total(db, session_id, session_data)
        elif tool_name == "check_policy":
            return await _check_policy(db, session_id, session_data)
        elif tool_name == "request_payment_approval":
            return await _request_payment_approval(db, session_id, session_data)
        elif tool_name == "get_payment_status":
            return await _get_payment_status(arguments, db, session_data)
        elif tool_name == "get_merchant_analytics":
            return await _get_merchant_analytics(db, session_id)
        elif tool_name == "get_sales_recommendations":
            return await _get_sales_recommendations(db, session_id)
        else:
            return json.dumps({"error": f"Unknown tool: {tool_name}"})
    except Exception as e:
        logger.error(f"Tool execution error ({tool_name}): {e}")
        return json.dumps({"error": f"Tool execution failed: {str(e)}"})


async def _search_products(arguments: Dict, db: AsyncSession, session_id: str, session_data: Dict) -> str:
    """Search products with optional filters."""
    query = select(Product).where(Product.stock > 0)

    category = arguments.get("category")
    max_price = arguments.get("max_price")
    min_price = arguments.get("min_price")

    if category:
        from sqlalchemy import or_
        query = query.where(or_(
            Product.category.ilike(f"%{category}%"),
            Product.subcategory.ilike(f"%{category}%"),
        ))
    if max_price is not None:
        query = query.where(Product.price <= max_price)
    if min_price is not None:
        query = query.where(Product.price >= min_price)

    search_text = arguments.get("query", "")
    if search_text:
        from sqlalchemy import or_
        search_filter = or_(
            Product.name.ilike(f"%{search_text}%"),
            Product.description.ilike(f"%{search_text}%"),
            Product.category.ilike(f"%{search_text}%"),
            Product.subcategory.ilike(f"%{search_text}%"),
            Product.tags.ilike(f"%{search_text}%"),
            Product.brand.ilike(f"%{search_text}%"),
        )
        query = query.where(search_filter)

    result = await db.execute(query.limit(10))
    products = result.scalars().all()

    products_list = []
    for p in products:
        products_list.append({
            "product_id": p.id,
            "name": p.name,
            "description": p.description,
            "category": p.category,
            "price": p.price,
            "currency": p.currency,
            "stock": p.stock,
            "position": len(products_list) + 1
        })

    session_data["last_search_results"] = products_list

    await log_audit_event(
        db, session_id, "PRODUCT_SEARCH",
        tool_called="search_products",
        input_data=json.dumps(arguments),
        decision=f"Found {len(products_list)} products",
        final_status="search_completed"
    )

    return json.dumps({
        "products": products_list,
        "count": len(products_list),
        "message": f"Found {len(products_list)} product(s)" + (f" in category '{category}'" if category else "") + (f" under ₹{max_price}" if max_price else "")
    })


async def _get_product_details(arguments: Dict, db: AsyncSession) -> str:
    """Get detailed product information."""
    product_id = arguments.get("product_id", "")
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()

    if not product:
        return json.dumps({"error": "Product not found"})

    return json.dumps({
        "product_id": product.id,
        "name": product.name,
        "description": product.description,
        "category": product.category,
        "price": product.price,
        "currency": product.currency,
        "stock": product.stock,
        "availability": product.stock > 0
    })


async def _check_inventory(arguments: Dict, db: AsyncSession) -> str:
    """Check inventory for a product."""
    product_id = arguments.get("product_id", "")
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()

    if not product:
        return json.dumps({"error": "Product not found"})

    return json.dumps({
        "product_id": product.id,
        "name": product.name,
        "stock": product.stock,
        "available": product.stock > 0,
        "status": "in_stock" if product.stock > 0 else "out_of_stock"
    })


async def _recommend_upsell(arguments: Dict, db: AsyncSession) -> str:
    """Get upsell recommendations (higher-tier alternatives)."""
    product_id = arguments.get("product_id", "")
    rels_result = await db.execute(
        select(ProductRelationship).where(
            ProductRelationship.product_id == product_id,
            ProductRelationship.relationship_type == "upsell"
        )
    )
    rels = rels_result.scalars().all()

    recommendations = []
    for rel in rels:
        product_result = await db.execute(select(Product).where(Product.id == rel.related_product_id))
        product = product_result.scalar_one_or_none()
        if product and product.stock > 0:
            recommendations.append({
                "product_id": product.id,
                "name": product.name,
                "price": product.price,
                "reason": rel.reason,
                "type": "upsell"
            })

    return json.dumps({"recommendations": recommendations, "count": len(recommendations)})


async def _recommend_cross_sell(arguments: Dict, db: AsyncSession) -> str:
    """Get cross-sell/complementary recommendations."""
    product_id = arguments.get("product_id", "")
    rels_result = await db.execute(
        select(ProductRelationship).where(
            ProductRelationship.product_id == product_id,
            ProductRelationship.relationship_type.in_(["cross-sell", "complementary"])
        )
    )
    rels = rels_result.scalars().all()

    recommendations = []
    for rel in rels:
        product_result = await db.execute(select(Product).where(Product.id == rel.related_product_id))
        product = product_result.scalar_one_or_none()
        if product and product.stock > 0:
            recommendations.append({
                "product_id": product.id,
                "name": product.name,
                "price": product.price,
                "reason": rel.reason,
                "type": rel.relationship_type
            })

    return json.dumps({"recommendations": recommendations, "count": len(recommendations)})


async def _add_to_cart(arguments: Dict, db: AsyncSession, session_id: str, session_data: Dict) -> str:
    """Add a product to the cart. Validates product, stock, and quantity."""
    product_id = arguments.get("product_id")
    product_position = arguments.get("product_position")
    quantity = arguments.get("quantity", 1)

    if not isinstance(quantity, int) or quantity < 1:
        return json.dumps({"error": "Quantity must be a positive integer"})
    if quantity > 100:
        return json.dumps({"error": "Maximum quantity is 100"})

    if not product_id and product_position:
        last_results = session_data.get("last_search_results", [])
        if product_position < 1 or product_position > len(last_results):
            return json.dumps({
                "error": f"Invalid position {product_position}. Only {len(last_results)} products in last search.",
                "available_positions": list(range(1, len(last_results) + 1))
            })
        product_id = last_results[product_position - 1]["product_id"]

    if not product_id:
        return json.dumps({"error": "Please specify a product to add (product_id or product_position)"})

    product_result = await db.execute(select(Product).where(Product.id == product_id))
    product = product_result.scalar_one_or_none()
    if not product:
        return json.dumps({"error": "Product not found"})
    if product.stock < quantity:
        return json.dumps({"error": f"Insufficient stock. Only {product.stock} available."})

    cart_id = session_data.get("cart_id")
    if cart_id:
        cart_result = await db.execute(select(Cart).where(Cart.id == cart_id))
        cart = cart_result.scalar_one_or_none()
        if not cart or cart.status != "active":
            cart = None

    if not cart_id or not cart:
        carts_result = await db.execute(
            select(Cart).where(Cart.session_id == session_id, Cart.status == "active")
        )
        cart = carts_result.scalar_one_or_none()

        if not cart:
            cart = Cart(session_id=session_id, total=0, status="active")
            db.add(cart)
            await db.commit()
            await db.refresh(cart)

        cart_id = cart.id
        session_data["cart_id"] = cart_id

    existing_result = await db.execute(
        select(CartItem).where(CartItem.cart_id == cart_id, CartItem.product_id == product_id)
    )
    existing = existing_result.scalar_one_or_none()

    if existing:
        new_qty = existing.quantity + quantity
        if new_qty > product.stock:
            return json.dumps({"error": f"Cannot add {quantity} more. Only {product.stock - existing.quantity} additional units available."})
        existing.quantity = new_qty
        existing.price_at_time = product.price
    else:
        cart_item = CartItem(
            cart_id=cart_id,
            product_id=product_id,
            quantity=quantity,
            price_at_time=product.price
        )
        db.add(cart_item)

    items_result = await db.execute(select(CartItem).where(CartItem.cart_id == cart_id))
    items = items_result.scalars().all()
    cart.total = sum(i.price_at_time * i.quantity for i in items)

    await db.commit()

    await log_audit_event(
        db, session_id, "CART_ITEM_ADDED",
        tool_called="add_to_cart",
        input_data=json.dumps({"product_id": product_id, "quantity": quantity}),
        decision=f"Added {product.name} x{quantity} to cart",
        final_status="cart_updated"
    )

    return json.dumps({
        "success": True,
        "product": {
            "product_id": product.id,
            "name": product.name,
            "price": product.price,
            "quantity": quantity,
            "subtotal": product.price * quantity
        },
        "cart": {
            "cart_id": cart_id,
            "total": cart.total,
            "item_count": sum(i.quantity for i in items)
        },
        "message": f"Added {product.name} x{quantity} to cart"
    })


async def _get_cart(db: AsyncSession, session_id: str, session_data: Dict) -> str:
    """Get current cart contents."""
    cart_id = session_data.get("cart_id")
    if not cart_id:
        return json.dumps({"cart": None, "message": "No cart found. Add some products first!"})

    cart_result = await db.execute(select(Cart).where(Cart.id == cart_id))
    cart = cart_result.scalar_one_or_none()
    if not cart or cart.status != "active":
        return json.dumps({"cart": None, "message": "No active cart found."})

    items_result = await db.execute(
        select(CartItem, Product).join(Product, CartItem.product_id == Product.id).where(CartItem.cart_id == cart_id)
    )
    rows = items_result.all()

    items = []
    for ci, p in rows:
        items.append({
            "product_id": ci.product_id,
            "name": p.name,
            "price": p.price,
            "quantity": ci.quantity,
            "subtotal": ci.price_at_time * ci.quantity
        })

    total = sum(i["subtotal"] for i in items)

    return json.dumps({
        "cart": {
            "cart_id": cart_id,
            "items": items,
            "total": total,
            "item_count": sum(i["quantity"] for i in items)
        }
    })


async def _calculate_cart_total(db: AsyncSession, session_id: str, session_data: Dict) -> str:
    """Calculate authoritative cart total server-side."""
    cart_id = session_data.get("cart_id")
    if not cart_id:
        return json.dumps({"error": "No cart found"})

    items_result = await db.execute(select(CartItem).where(CartItem.cart_id == cart_id))
    items = items_result.scalars().all()

    total = sum(i.price_at_time * i.quantity for i in items)

    cart_result = await db.execute(select(Cart).where(Cart.id == cart_id))
    cart = cart_result.scalar_one_or_none()
    if cart:
        cart.total = total
        await db.commit()

    return json.dumps({
        "cart_id": cart_id,
        "total": total,
        "currency": "INR",
        "item_count": sum(i.quantity for i in items)
    })


async def _check_policy(db: AsyncSession, session_id: str, session_data: Dict) -> str:
    """Check if cart total is within policy limits."""
    cart_id = session_data.get("cart_id")
    if not cart_id:
        return json.dumps({"error": "No cart found"})

    cart_result = await db.execute(select(Cart).where(Cart.id == cart_id))
    cart = cart_result.scalar_one_or_none()
    if not cart:
        return json.dumps({"error": "Cart not found"})

    policy_result = await db.execute(select(Policy).limit(1))
    policy = policy_result.scalar_one_or_none()
    if not policy:
        policy = Policy(max_transaction_amount=3000, payment_requires_approval=True)

    allowed = cart.total <= policy.max_transaction_amount
    reason = "Policy check passed" if allowed else f"Transaction amount ₹{cart.total:.0f} exceeds spending limit ₹{policy.max_transaction_amount:.0f}"

    await log_audit_event(
        db, session_id, "POLICY_CHECK",
        tool_called="check_policy",
        input_data=json.dumps({"cart_total": cart.total, "limit": policy.max_transaction_amount}),
        decision="ALLOWED" if allowed else "BLOCKED",
        policy_result=reason,
        final_status="policy_passed" if allowed else "policy_blocked"
    )

    return json.dumps({
        "allowed": allowed,
        "reason": reason,
        "cart_total": cart.total,
        "spending_limit": policy.max_transaction_amount,
        "currency": "INR"
    })


async def _request_payment_approval(db: AsyncSession, session_id: str, session_data: Dict) -> str:
    """Create an order and request user approval before payment."""
    cart_id = session_data.get("cart_id")
    if not cart_id:
        return json.dumps({"error": "No cart found. Add products first."})

    cart_result = await db.execute(select(Cart).where(Cart.id == cart_id))
    cart = cart_result.scalar_one_or_none()
    if not cart or cart.status != "active":
        return json.dumps({"error": "Cart not found or not active"})

    existing_order_result = await db.execute(
        select(Order).where(
            Order.cart_id == cart_id,
            Order.status.in_(["approved", "payment_initiated", "success"])
        )
    )
    existing_order = existing_order_result.scalar_one_or_none()
    if existing_order:
        return json.dumps({
            "error": "An order is already approved or in progress for this cart",
            "order_id": existing_order.id,
            "status": existing_order.status
        })

    policy_result = await db.execute(select(Policy).limit(1))
    policy = policy_result.scalar_one_or_none()
    if not policy:
        policy = Policy(max_transaction_amount=3000, payment_requires_approval=True)

    if cart.total > policy.max_transaction_amount:
        return json.dumps({
            "error": f"Cart total ₹{cart.total:.0f} exceeds spending limit ₹{policy.max_transaction_amount:.0f}. Cannot request approval.",
            "allowed": False
        })

    order = Order(
        cart_id=cart.id,
        customer_id=cart.customer_id,
        merchant_id="merchant_001",
        total=cart.total,
        status="approval_pending"
    )
    db.add(order)
    await db.commit()
    await db.refresh(order)

    session_data["last_order_id"] = order.id

    token = str(uuid.uuid4())
    approval = Approval(
        order_id=order.id,
        session_id=session_id,
        status="pending",
        token=token
    )
    db.add(approval)
    await db.commit()
    await db.refresh(approval)

    session_data["last_approval_id"] = approval.id

    await log_audit_event(
        db, session_id, "APPROVAL_REQUESTED",
        tool_called="request_payment_approval",
        input_data=json.dumps({"cart_id": cart_id, "order_id": order.id, "total": cart.total}),
        decision="approval_pending",
        policy_result="within_limit",
        approval_status="pending",
        final_status="approval_requested"
    )

    return json.dumps({
        "approval_id": approval.id,
        "order_id": order.id,
        "token": token,
        "status": "pending",
        "total": cart.total,
        "message": f"Payment approval requested for ₹{cart.total:.0f}. Please approve to proceed.",
        "requires_user_approval": True
    })


async def _get_payment_status(arguments: Dict, db: AsyncSession, session_data: Dict) -> str:
    """Get payment/order status."""
    order_id = arguments.get("order_id") or session_data.get("last_order_id")
    if not order_id:
        return json.dumps({"error": "No order ID provided"})

    order_result = await db.execute(select(Order).where(Order.id == order_id))
    order = order_result.scalar_one_or_none()
    if not order:
        return json.dumps({"error": "Order not found"})

    return json.dumps({
        "order_id": order.id,
        "status": order.status,
        "total": order.total,
        "razorpay_order_id": order.razorpay_order_id,
        "razorpay_payment_id": order.razorpay_payment_id
    })


# ────────────────────────────────────────────────────────
# Merchant Analytics Tools
# ────────────────────────────────────────────────────────

async def _get_merchant_analytics(db: AsyncSession, session_id: str) -> str:
    """Get merchant business analytics from real order data."""
    # Get successful orders
    orders_result = await db.execute(select(Order).where(Order.status == "success"))
    successful_orders = orders_result.scalars().all()

    all_orders_result = await db.execute(select(Order))
    all_orders = all_orders_result.scalars().all()

    # Revenue
    total_revenue = sum(float(o.total or 0) for o in successful_orders)
    
    # Products
    products_result = await db.execute(select(Product))
    products = products_result.scalars().all()
    products_map = {p.id: p for p in products}
    
    # Calculate actual sales from orders
    product_sales = {}
    product_revenue = {}
    total_products_sold = 0
    for order in successful_orders:
        items_result = await db.execute(select(OrderItem).where(OrderItem.order_id == order.id))
        items = items_result.scalars().all()
        for item in items:
            pid = item.product_id
            qty = int(item.quantity or 0)
            product_sales[pid] = product_sales.get(pid, 0) + qty
            product_revenue[pid] = product_revenue.get(pid, 0) + float(item.subtotal or 0)
            total_products_sold += qty

    # COGS
    total_cogs = 0.0
    for order in successful_orders:
        items_result = await db.execute(select(OrderItem).where(OrderItem.order_id == order.id))
        items = items_result.scalars().all()
        for item in items:
            product = products_map.get(item.product_id)
            if product and product.cost_price and product.cost_price > 0:
                total_cogs += float(product.cost_price) * int(item.quantity or 0)

    profit = total_revenue - total_cogs
    margin = (profit / total_revenue * 100) if total_revenue > 0 else 0

    # Best sellers
    best_sellers = []
    for pid in sorted(product_sales.keys(), key=lambda p: product_sales[p], reverse=True)[:5]:
        p = products_map.get(pid)
        if p:
            best_sellers.append({
                "name": p.name,
                "sales": product_sales[pid],
                "revenue": round(product_revenue.get(pid, 0), 2),
                "category": p.category,
                "stock": p.stock,
            })

    # Low stock
    low_stock = [{"name": p.name, "stock": p.stock, "category": p.category}
                 for p in products if 0 < p.stock <= 10]

    # Categories
    cat_revenue = {}
    for pid, rev in product_revenue.items():
        p = products_map.get(pid)
        if p:
            cat_revenue[p.category] = cat_revenue.get(p.category, 0) + rev
    top_categories = sorted(cat_revenue.items(), key=lambda x: x[1], reverse=True)[:5]

    analytics = {
        "total_revenue": round(total_revenue, 2),
        "total_orders": len(all_orders),
        "completed_orders": len(successful_orders),
        "products_sold": total_products_sold,
        "total_products": len(products),
        "profit": round(profit, 2),
        "margin": round(margin, 2),
        "cogs": round(total_cogs, 2),
        "best_sellers": best_sellers,
        "low_stock_products": low_stock,
        "top_categories": [{"category": c, "revenue": round(r, 2)} for c, r in top_categories],
    }

    await log_audit_event(
        db, session_id, "ANALYTICS_VIEWED",
        tool_called="get_merchant_analytics",
        decision=f"Revenue: ₹{total_revenue:.0f}, Products sold: {total_products_sold}",
        final_status="success"
    )

    return json.dumps(analytics)


async def _get_sales_recommendations(db: AsyncSession, session_id: str) -> str:
    """Generate sales growth recommendations based on real data."""
    # Get all products
    products_result = await db.execute(select(Product))
    products = products_result.scalars().all()
    products_map = {p.id: p for p in products}

    # Get successful orders
    orders_result = await db.execute(select(Order).where(Order.status == "success"))
    successful_orders = orders_result.scalars().all()

    # Calculate actual sales
    product_sales = {}
    product_revenue = {}
    for order in successful_orders:
        items_result = await db.execute(select(OrderItem).where(OrderItem.order_id == order.id))
        items = items_result.scalars().all()
        for item in items:
            pid = item.product_id
            product_sales[pid] = product_sales.get(pid, 0) + int(item.quantity or 0)
            product_revenue[pid] = product_revenue.get(pid, 0) + float(item.subtotal or 0)

    recommendations = []

    # 🚀 SELL MORE - High performing products
    top_performers = sorted(product_sales.items(), key=lambda x: x[1], reverse=True)[:3]
    for pid, sales in top_performers:
        p = products_map.get(pid)
        if p and p.stock > 0:
            recommendations.append({
                "type": "sell_more",
                "icon": "🚀",
                "title": f"SELL MORE: {p.name}",
                "message": f"{p.name} is performing strongly with {sales} units sold. Promote it today.",
                "product_id": pid,
                "product_name": p.name,
                "category": p.category,
                "sales": sales,
                "reason": "High sales velocity indicates strong customer demand.",
            })

    # 💰 HIGH PROFIT - Products with highest margin
    margin_products = []
    for p in products:
        if p.cost_price and p.cost_price > 0 and p.price > 0:
            margin = ((p.price - p.cost_price) / p.price) * 100
            margin_products.append((p, margin, product_revenue.get(p.id, 0)))
    margin_products.sort(key=lambda x: x[1], reverse=True)
    for p, margin, rev in margin_products[:2]:
        if margin > 20:
            recommendations.append({
                "type": "high_profit",
                "icon": "💰",
                "title": f"HIGH PROFIT: {p.name}",
                "message": f"{p.name} has a {margin:.0f}% profit margin. This is one of your most profitable products.",
                "product_id": p.id,
                "product_name": p.name,
                "margin": round(margin, 1),
                "revenue": round(rev, 2),
                "reason": f"Highest margin at {margin:.0f}%.",
            })

    # 📦 RESTOCK - Products selling quickly with low stock
    for pid, sales in sorted(product_sales.items(), key=lambda x: x[1], reverse=True)[:5]:
        p = products_map.get(pid)
        if p and 0 < p.stock <= 10 and sales > 3:
            recommendations.append({
                "type": "restock",
                "icon": "📦",
                "title": f"RESTOCK: {p.name}",
                "message": f"{p.name} is selling quickly ({sales} sold) and stock is low ({p.stock} left).",
                "product_id": pid,
                "product_name": p.name,
                "stock": p.stock,
                "sales": sales,
                "reason": f"High demand with limited stock remaining.",
            })

    # 🐢 SLOW MOVING - Products with low sales relative to stock
    for p in products:
        if p.stock > 20:
            sales = product_sales.get(p.id, 0)
            if sales < 2:
                recommendations.append({
                    "type": "slow_moving",
                    "icon": "🐢",
                    "title": f"SLOW MOVER: {p.name}",
                    "message": f"{p.name} has {p.stock} units in stock but only {sales} sold. Consider a promotion or bundle.",
                    "product_id": p.id,
                    "product_name": p.name,
                    "stock": p.stock,
                    "sales": sales,
                    "reason": "Low sales velocity with high stock levels.",
                })

    # Ensure at least one recommendation
    if not recommendations:
        recommendations.append({
            "type": "insufficient_data",
            "icon": "📊",
            "title": "Need More Data",
            "message":            "Not enough sales data yet. Complete more orders to generate reliable recommendations.",
            "reason": "Recommendations require order data to analyze patterns.",
        })

    # Limit to 8 recommendations
    recommendations = recommendations[:8]

    await log_audit_event(
        db, session_id,        "RECOMMENDATIONS",
        tool_called="get_sales_recommendations",
        decision=f"Generated {len(recommendations)} recommendations",
        final_status="success"
    )

    return json.dumps({"recommendations": recommendations, "count": len(recommendations)})
