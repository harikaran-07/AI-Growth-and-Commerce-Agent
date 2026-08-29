from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.database import get_db
from models.models import Cart, CartItem, Product
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timezone

router = APIRouter()

class CartItemCreate(BaseModel):
    product_id: str
    quantity: int = 1

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

@router.post("/", response_model=CartResponse)
async def create_cart(session_id: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    cart = Cart(session_id=session_id or "anonymous", total=0)
    db.add(cart)
    await db.commit()
    await db.refresh(cart)
    return CartResponse(id=cart.id, status=cart.status, total=0, items=[], item_count=0)

@router.post("/{cart_id}/items", response_model=CartItemResponse)
async def add_to_cart(cart_id: str, item: CartItemCreate, db: AsyncSession = Depends(get_db)):
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
        raise HTTPException(status_code=400, detail="Insufficient stock")
    
    existing_result = await db.execute(
        select(CartItem).where(CartItem.cart_id == cart_id, CartItem.product_id == item.product_id)
    )
    existing = existing_result.scalar_one_or_none()
    
    if existing:
        existing.quantity += item.quantity
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
    
    cart_items_result = await db.execute(select(CartItem).where(CartItem.cart_id == cart_id))
    cart_items = cart_items_result.scalars().all()
    
    return CartItemResponse(
        id=existing.id if existing else cart_items[-1].id,
        product_id=item.product_id,
        product_name=product.name,
        quantity=existing.quantity if existing else item.quantity,
        price_at_time=product.price,
        subtotal=product.price * (existing.quantity if existing else item.quantity)
    )

@router.get("/{cart_id}", response_model=CartResponse)
async def get_cart(cart_id: str, db: AsyncSession = Depends(get_db)):
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
    
    return CartResponse(
        id=cart.id,
        status=cart.status,
        total=cart.total,
        items=items,
        item_count=sum(i.quantity for i in items)
    )
