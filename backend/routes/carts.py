"""
Cart endpoints with proper quantity validation.
Includes session-based endpoints for frontend convenience.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.database import get_db
from models.models import Cart, CartItem, Product
from pydantic import BaseModel, field_validator
from typing import List, Optional
from datetime import datetime, timezone

router = APIRouter()


class CartItemCreate(BaseModel):
    product_id: str
    quantity: int = 1

    @field_validator('quantity')
    @classmethod
    def validate_quantity(cls, v):
        if not isinstance(v, int) or v < 1:
            raise ValueError('Quantity must be a positive integer')
        if v > 100:
            raise ValueError('Maximum quantity is 100')
        return v


class CartItemUpdate(BaseModel):
    quantity: int

    @field_validator('quantity')
    @classmethod
    def validate_quantity(cls, v):
        if not isinstance(v, int) or v < 1:
            raise ValueError('Quantity must be a positive integer')
        if v > 100:
            raise ValueError('Maximum quantity is 100')
        return v


class CartItemResponse(BaseModel):
    id: str
    product_id: str
    product_name: str
    quantity: int
    price_at_time: float
    subtotal: float


class CartResponse(BaseModel):
    id: str
    status: str
    total: float
    items: List[CartItemResponse]
    item_count: int


async def _get_or_create_cart(db: AsyncSession, session_id: str) -> Cart:
    """Get or create an active cart for a session."""
    result = await db.execute(
        select(Cart).where(Cart.session_id == session_id, Cart.status == "active")
    )
    cart = result.scalar_one_or_none()
    if not cart:
        cart = Cart(session_id=session_id, total=0, status="active")
        db.add(cart)
        await db.commit()
        await db.refresh(cart)
    return cart


async def _build_cart_response(db: AsyncSession, cart: Cart) -> CartResponse:
    """Build a full cart response with items."""
    items_result = await db.execute(
        select(CartItem, Product).join(Product, CartItem.product_id == Product.id).where(CartItem.cart_id == cart.id)
    )
    rows = items_result.all()
    items = []
    for ci, p in rows:
        items.append(CartItemResponse(
            id=ci.id,
            product_id=ci.product_id,
            product_name=p.name,
            quantity=ci.quantity,
            price_at_time=ci.price_at_time,
            subtotal=ci.price_at_time * ci.quantity
        ))
    total = sum(i.subtotal for i in items)
    cart.total = total
    await db.commit()
    return CartResponse(
        id=cart.id,
        status=cart.status,
        total=total,
        items=items,
        item_count=sum(i.quantity for i in items)
    )


# ────────────────────────────────────────────────────────
# Session-based endpoints (used by frontend)
# ────────────────────────────────────────────────────────

@router.post("/session/{session_id}/add")
async def add_to_cart_by_session(session_id: str, item: CartItemCreate, db: AsyncSession = Depends(get_db)):
    """Add item to cart using session_id (frontend convenience endpoint)."""
    cart = await _get_or_create_cart(db, session_id)

    product_result = await db.execute(select(Product).where(Product.id == item.product_id))
    product = product_result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    if product.stock < item.quantity:
        raise HTTPException(status_code=400, detail=f"Insufficient stock. Only {product.stock} available.")

    existing_result = await db.execute(
        select(CartItem).where(CartItem.cart_id == cart.id, CartItem.product_id == item.product_id)
    )
    existing = existing_result.scalar_one_or_none()

    if existing:
        new_qty = existing.quantity + item.quantity
        if new_qty > product.stock:
            raise HTTPException(status_code=400, detail=f"Cannot add {item.quantity} more.")
        existing.quantity = new_qty
        existing.price_at_time = product.price
    else:
        cart_item = CartItem(
            cart_id=cart.id,
            product_id=item.product_id,
            quantity=item.quantity,
            price_at_time=product.price
        )
        db.add(cart_item)

    await db.commit()
    return await _build_cart_response(db, cart)


@router.get("/session/{session_id}")
async def get_cart_by_session(session_id: str, db: AsyncSession = Depends(get_db)):
    """Get cart contents using session_id."""
    cart = await _get_or_create_cart(db, session_id)
    return await _build_cart_response(db, cart)


@router.patch("/session/{session_id}/item/{product_id}")
async def update_cart_item(session_id: str, product_id: str, update: CartItemUpdate, db: AsyncSession = Depends(get_db)):
    """Update item quantity in cart."""
    cart = await _get_or_create_cart(db, session_id)

    item_result = await db.execute(
        select(CartItem).where(CartItem.cart_id == cart.id, CartItem.product_id == product_id)
    )
    item = item_result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Item not in cart")

    product_result = await db.execute(select(Product).where(Product.id == product_id))
    product = product_result.scalar_one_or_none()
    if product and update.quantity > product.stock:
        raise HTTPException(status_code=400, detail=f"Only {product.stock} in stock.")

    if update.quantity <= 0:
        await db.delete(item)
    else:
        item.quantity = update.quantity
        if product:
            item.price_at_time = product.price

    await db.commit()
    return await _build_cart_response(db, cart)


@router.delete("/session/{session_id}/item/{product_id}")
async def remove_cart_item(session_id: str, product_id: str, db: AsyncSession = Depends(get_db)):
    """Remove item from cart."""
    cart = await _get_or_create_cart(db, session_id)

    item_result = await db.execute(
        select(CartItem).where(CartItem.cart_id == cart.id, CartItem.product_id == product_id)
    )
    item = item_result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Item not in cart")

    await db.delete(item)
    await db.commit()
    return await _build_cart_response(db, cart)


@router.delete("/session/{session_id}/clear")
async def clear_cart(session_id: str, db: AsyncSession = Depends(get_db)):
    """Clear all items from cart."""
    cart = await _get_or_create_cart(db, session_id)
    items_result = await db.execute(select(CartItem).where(CartItem.cart_id == cart.id))
    items = items_result.scalars().all()
    for item in items:
        await db.delete(item)
    cart.total = 0
    await db.commit()
    return await _build_cart_response(db, cart)


# ────────────────────────────────────────────────────────
# Original cart_id-based endpoints (backward compatible)
# ────────────────────────────────────────────────────────

@router.post("/", response_model=CartResponse)
async def create_cart(session_id: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    """Create a new empty cart."""
    cart = Cart(session_id=session_id or "anonymous", total=0)
    db.add(cart)
    await db.commit()
    await db.refresh(cart)
    return CartResponse(id=cart.id, status=cart.status, total=0, items=[], item_count=0)


@router.post("/{cart_id}/items", response_model=CartItemResponse)
async def add_to_cart(cart_id: str, item: CartItemCreate, db: AsyncSession = Depends(get_db)):
    """Add an item to the cart with server-side validation."""
    cart_result = await db.execute(select(Cart).where(Cart.id == cart_id))
    cart = cart_result.scalar_one_or_none()
    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")
    if cart.status != "active":
        raise HTTPException(status_code=400, detail="Cart is not active")

    product_result = await db.execute(select(Product).where(Product.id == item.product_id))
    product = product_result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    if product.stock < item.quantity:
        raise HTTPException(status_code=400, detail=f"Insufficient stock. Only {product.stock} available.")

    existing_result = await db.execute(
        select(CartItem).where(CartItem.cart_id == cart_id, CartItem.product_id == item.product_id)
    )
    existing = existing_result.scalar_one_or_none()

    if existing:
        new_qty = existing.quantity + item.quantity
        if new_qty > product.stock:
            raise HTTPException(status_code=400, detail=f"Cannot add {item.quantity} more.")
        existing.quantity = new_qty
        existing.price_at_time = product.price
    else:
        cart_item = CartItem(
            cart_id=cart_id,
            product_id=item.product_id,
            quantity=item.quantity,
            price_at_time=product.price
        )
        db.add(cart_item)

    await db.commit()
    items_result = await db.execute(select(CartItem).where(CartItem.cart_id == cart_id))
    items = items_result.scalars().all()
    cart.total = sum(i.price_at_time * i.quantity for i in items)
    await db.commit()
    await db.refresh(cart)

    return CartItemResponse(
        id=existing.id if existing else cart_item.id,
        product_id=item.product_id,
        product_name=product.name,
        quantity=existing.quantity if existing else item.quantity,
        price_at_time=product.price,
        subtotal=product.price * (existing.quantity if existing else item.quantity)
    )


@router.get("/{cart_id}", response_model=CartResponse)
async def get_cart(cart_id: str, db: AsyncSession = Depends(get_db)):
    """Get cart contents with items."""
    cart_result = await db.execute(select(Cart).where(Cart.id == cart_id))
    cart = cart_result.scalar_one_or_none()
    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")

    items_result = await db.execute(
        select(CartItem, Product).join(Product, CartItem.product_id == Product.id).where(CartItem.cart_id == cart_id)
    )
    rows = items_result.all()
    items = []
    for ci, p in rows:
        items.append(CartItemResponse(
            id=ci.id,
            product_id=ci.product_id,
            product_name=p.name,
            quantity=ci.quantity,
            price_at_time=ci.price_at_time,
            subtotal=ci.price_at_time * ci.quantity
        ))

    total = sum(i.subtotal for i in items)
    cart.total = total
    await db.commit()

    return CartResponse(
        id=cart.id,
        status=cart.status,
        total=total,
        items=items,
        item_count=sum(i.quantity for i in items)
    )
