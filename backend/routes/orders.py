"""
Orders endpoints - list, detail, create from checkout.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from models.database import get_db
from models.models import Order, OrderItem, Cart, CartItem, Product, Payment
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

router = APIRouter()


class OrderItemResponse(BaseModel):
    id: str
    product_id: str
    product_name: str
    quantity: int
    price: float
    subtotal: float


class OrderResponse(BaseModel):
    id: str
    cart_id: Optional[str] = None
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None
    customer_phone: Optional[str] = None
    customer_address: Optional[str] = None
    subtotal: float
    discount: float
    tax: float
    shipping: float
    total: float
    status: str
    payment_status: str
    razorpay_order_id: Optional[str] = None
    razorpay_payment_id: Optional[str] = None
    items: List[OrderItemResponse] = []
    created_at: datetime

    class Config:
        from_attributes = True


class OrderListResponse(BaseModel):
    orders: List[OrderResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class CheckoutRequest(BaseModel):
    session_id: str
    customer_name: str
    customer_email: str
    customer_phone: Optional[str] = ""
    customer_address: Optional[str] = ""
    discount: float = 0

    class Config:
        # Validate fields
        json_schema_extra = {
            "example": {
                "session_id": "sess_123",
                "customer_name": "John Doe",
                "customer_email": "john@example.com",
                "customer_phone": "+919876543210",
                "customer_address": "123 Main St, City"
            }
        }


@router.get("/", response_model=OrderListResponse)
async def list_orders(
    status: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db)
):
    """List all orders with pagination."""
    query = select(Order)
    count_query = select(func.count(Order.id))

    if status:
        query = query.where(Order.status == status)
        count_query = count_query.where(Order.status == status)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.order_by(Order.created_at.desc())
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    result = await db.execute(query)
    orders = result.scalars().all()

    order_responses = []
    for order in orders:
        items_result = await db.execute(
            select(OrderItem).where(OrderItem.order_id == order.id)
        )
        items = items_result.scalars().all()
        order_responses.append(OrderResponse(
            id=order.id,
            cart_id=order.cart_id,
            customer_name=order.customer_name,
            customer_email=order.customer_email,
            customer_phone=order.customer_phone,
            customer_address=order.customer_address,
            subtotal=order.subtotal or 0,
            discount=order.discount or 0,
            tax=order.tax or 0,
            shipping=order.shipping or 0,
            total=order.total,
            status=order.status or "pending",
            payment_status=order.payment_status or "pending",
            razorpay_order_id=order.razorpay_order_id,
            razorpay_payment_id=order.razorpay_payment_id,
            items=[OrderItemResponse(
                id=i.id, product_id=i.product_id, product_name=i.product_name,
                quantity=i.quantity, price=i.price, subtotal=i.subtotal
            ) for i in items],
            created_at=order.created_at
        ))

    return OrderListResponse(
        orders=order_responses,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.get("/stats")
async def order_stats(db: AsyncSession = Depends(get_db)):
    """Get order statistics for dashboard."""
    total = await db.execute(select(func.count(Order.id)))
    total_orders = total.scalar() or 0

    success_result = await db.execute(
        select(func.count(Order.id)).where(Order.status == "success")
    )
    success_orders = success_result.scalar() or 0

    revenue_result = await db.execute(
        select(func.sum(Order.total)).where(Order.status == "success")
    )
    total_revenue = revenue_result.scalar() or 0

    avg_result = await db.execute(
        select(func.avg(Order.total)).where(Order.status == "success")
    )
    avg_order_value = avg_result.scalar() or 0

    pending_result = await db.execute(
        select(func.count(Order.id)).where(Order.status.in_(["pending", "processing"]))
    )
    pending_orders = pending_result.scalar() or 0

    return {
        "total_orders": total_orders,
        "success_orders": success_orders,
        "total_revenue": round(total_revenue, 2),
        "avg_order_value": round(avg_order_value, 2),
        "pending_orders": pending_orders,
    }


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(order_id: str, db: AsyncSession = Depends(get_db)):
    """Get order details."""
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    items_result = await db.execute(
        select(OrderItem).where(OrderItem.order_id == order.id)
    )
    items = items_result.scalars().all()

    return OrderResponse(
        id=order.id,
        cart_id=order.cart_id,
        customer_name=order.customer_name,
        customer_email=order.customer_email,
        customer_phone=order.customer_phone,
        customer_address=order.customer_address,
        subtotal=order.subtotal or 0,
        discount=order.discount or 0,
        tax=order.tax or 0,
        shipping=order.shipping or 0,
        total=order.total,
        status=order.status or "pending",
        payment_status=order.payment_status or "pending",
        razorpay_order_id=order.razorpay_order_id,
        razorpay_payment_id=order.razorpay_payment_id,
        items=[OrderItemResponse(
            id=i.id, product_id=i.product_id, product_name=i.product_name,
            quantity=i.quantity, price=i.price, subtotal=i.subtotal
        ) for i in items],
        created_at=order.created_at
    )


def _validate_checkout_fields(request: CheckoutRequest):
    """Validate all checkout fields."""
    errors = []
    if not request.customer_name or not request.customer_name.strip():
        errors.append("Full name is required")
    if not request.customer_email or "@" not in request.customer_email:
        errors.append("Valid email is required")
    if not request.session_id:
        errors.append("Session is required")
    return errors


@router.post("/checkout", response_model=OrderResponse)
async def checkout(request: CheckoutRequest, db: AsyncSession = Depends(get_db)):
    """Create an order from the current cart with full validation."""
    # Validate input fields
    validation_errors = _validate_checkout_fields(request)
    if validation_errors:
        raise HTTPException(status_code=400, detail="; ".join(validation_errors))

    # Find the active cart for this session
    cart_result = await db.execute(
        select(Cart).where(Cart.session_id == request.session_id, Cart.status == "active")
    )
    cart = cart_result.scalar_one_or_none()
    if not cart:
        raise HTTPException(status_code=404, detail="No active cart found")

    # Get cart items with product details
    items_result = await db.execute(
        select(CartItem, Product).join(Product, CartItem.product_id == Product.id).where(CartItem.cart_id == cart.id)
    )
    rows = items_result.all()
    if not rows:
        raise HTTPException(status_code=400, detail="Cart is empty. Add products before checkout.")

    # Validate stock and calculate totals SERVER-SIDE
    # Never trust price/quantity from browser
    subtotal = 0
    order_items = []
    for ci, p in rows:
        # Re-verify stock from database
        if p.stock < ci.quantity:
            raise HTTPException(status_code=400, detail=f"Insufficient stock for {p.name}. Only {p.stock} available.")
        # Use server-side price, never client price
        item_subtotal = p.price * ci.quantity
        subtotal += item_subtotal
        order_items.append({
            "product_id": p.id,
            "product_name": p.name,
            "quantity": ci.quantity,
            "price": p.price,
            "subtotal": item_subtotal,
        })

    # Validate price integrity
    if subtotal <= 0:
        raise HTTPException(status_code=400, detail="Order total must be greater than zero")

    # Calculate tax (18% GST) and shipping server-side
    discount = min(request.discount, subtotal * 0.1) if request.discount else 0  # Max 10% discount
    taxable = subtotal - discount
    tax = round(taxable * 0.18, 2)
    shipping = 0 if subtotal >= 500 else 49.0
    total = round(taxable + tax + shipping, 2)

    # Create order
    order = Order(
        cart_id=cart.id,
        customer_name=request.customer_name.strip(),
        customer_email=request.customer_email.strip().lower(),
        customer_phone=(request.customer_phone or "").strip(),
        customer_address=(request.customer_address or "").strip(),
        subtotal=subtotal,
        discount=discount,
        tax=tax,
        shipping=shipping,
        total=total,
        status="pending",
        payment_status="pending",
    )
    db.add(order)
    await db.commit()
    await db.refresh(order)

    # Create order items
    for item_data in order_items:
        order_item = OrderItem(
            order_id=order.id,
            product_id=item_data["product_id"],
            product_name=item_data["product_name"],
            quantity=item_data["quantity"],
            price=item_data["price"],
            subtotal=item_data["subtotal"],
        )
        db.add(order_item)
    await db.commit()

    # Mark cart as completed
    cart.status = "completed"
    await db.commit()

    # Create audit log
    from models.models import AuditLog
    audit = AuditLog(
        action="ORDER_CREATED",
        description=f"Order {order.id} created from cart {cart.id}, total: {total}",
        event_type="order",
        related_entity=order.id,
        financial_impact=total,
        final_status="pending",
    )
    db.add(audit)
    await db.commit()

    return OrderResponse(
        id=order.id,
        cart_id=order.cart_id,
        customer_name=order.customer_name,
        customer_email=order.customer_email,
        customer_phone=order.customer_phone,
        customer_address=order.customer_address,
        subtotal=order.subtotal,
        discount=order.discount,
        tax=order.tax,
        shipping=order.shipping,
        total=order.total,
        status=order.status,
        payment_status=order.payment_status,
        items=[OrderItemResponse(
            id=oi["product_id"], product_id=oi["product_id"], product_name=oi["product_name"],
            quantity=oi["quantity"], price=oi["price"], subtotal=oi["subtotal"]
        ) for oi in order_items],
        created_at=order.created_at,
    )


@router.patch("/{order_id}/status")
async def update_order_status(order_id: str, status: str, db: AsyncSession = Depends(get_db)):
    """Update order status."""
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    order.status = status
    await db.commit()
    return {"status": "updated", "order_id": order_id, "new_status": status}
