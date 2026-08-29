from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.database import get_db
from models.models import Product, ProductRelationship, Cart, CartItem, Order, Policy, Approval, AuditLog, Customer
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timezone
import uuid
import json

router = APIRouter()

class SearchRequest(BaseModel):
    query: str
    max_price: Optional[float] = None
    category: Optional[str] = None
    session_id: str

class SearchResponse(BaseModel):
    products: List[dict]
    recommendations: List[dict]

class CartRequest(BaseModel):
    session_id: str
    product_ids: List[str]
    quantities: List[int] = []

class CartResponse(BaseModel):
    cart_id: str
    items: List[dict]
    total: float

class PaymentRequest(BaseModel):
    cart_id: str
    session_id: str

class PolicyCheckResponse(BaseModel):
    allowed: bool
    reason: str
    total: float
    limit: float

class ApprovalResponse(BaseModel):
    approval_id: str
    token: str
    status: str
    message: str

@router.post("/search", response_model=SearchResponse)
async def search_products(request: SearchRequest, db: AsyncSession = Depends(get_db)):
    query = select(Product).where(Product.stock > 0)
    if request.max_price:
        query = query.where(Product.price <= request.max_price)
    if request.category:
        query = query.where(Product.category == request.category)
    
    result = await db.execute(query)
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
            "stock": p.stock
        })
    
    recommendations = []
    if products:
        first_product = products[0]
        rels_result = await db.execute(
            select(ProductRelationship).where(ProductRelationship.product_id == first_product.id)
        )
        rels = rels_result.scalars().all()
        for rel in rels:
            rel_product_result = await db.execute(
                select(Product).where(Product.id == rel.related_product_id)
            )
            rel_product = rel_product_result.scalar_one_or_none()
            if rel_product and rel_product.stock > 0:
                recommendations.append({
                    "product_id": rel_product.id,
                    "name": rel_product.name,
                    "price": rel_product.price,
                    "reason": rel.reason,
                    "type": rel.relationship_type
                })
    
    return SearchResponse(products=products_list, recommendations=recommendations)

@router.post("/recommend")
async def recommend_product(request: dict, db: AsyncSession = Depends(get_db)):
    product_id = request.get("product_id")
    recommendation_type = request.get("type", "cross-sell")
    
    rels_result = await db.execute(
        select(ProductRelationship).where(
            ProductRelationship.product_id == product_id,
            ProductRelationship.relationship_type == recommendation_type
        )
    )
    rels = rels_result.scalars().all()
    
    recommendations = []
    for rel in rels:
        product_result = await db.execute(
            select(Product).where(Product.id == rel.related_product_id)
        )
        product = product_result.scalar_one_or_none()
        if product and product.stock > 0:
            recommendations.append({
                "product_id": product.id,
                "name": product.name,
                "price": product.price,
                "reason": rel.reason,
                "type": rel.relationship_type
            })
    
    return {"recommendations": recommendations}

@router.post("/cart", response_model=CartResponse)
async def create_agent_cart(request: CartRequest, db: AsyncSession = Depends(get_db)):
    cart = Cart(session_id=request.session_id, total=0)
    db.add(cart)
    await db.commit()
    await db.refresh(cart)
    
    items = []
    total = 0
    for i, pid in enumerate(request.product_ids):
        product_result = await db.execute(select(Product).where(Product.id == pid))
        product = product_result.scalar_one_or_none()
        if not product or product.stock <= 0:
            continue
        
        qty = request.quantities[i] if i < len(request.quantities) else 1
        cart_item = CartItem(
            cart_id=cart.id,
            product_id=pid,
            quantity=qty,
            price_at_time=product.price
        )
        db.add(cart_item)
        items.append({
            "product_id": pid,
            "name": product.name,
            "price": product.price,
            "quantity": qty,
            "subtotal": product.price * qty
        })
        total += product.price * qty
    
    cart.total = total
    await db.commit()
    
    return CartResponse(cart_id=cart.id, items=items, total=total)

@router.post("/policy-check", response_model=PolicyCheckResponse)
async def check_policy(request: PaymentRequest, db: AsyncSession = Depends(get_db)):
    cart_result = await db.execute(select(Cart).where(Cart.id == request.cart_id))
    cart = cart_result.scalar_one_or_none()
    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")
    
    policy_result = await db.execute(select(Policy).limit(1))
    policy = policy_result.scalar_one_or_none()
    if not policy:
        policy = Policy(max_transaction_amount=3000, payment_requires_approval=True)
    
    if cart.total > policy.max_transaction_amount:
        return PolicyCheckResponse(
            allowed=False,
            reason=f"Transaction amount ₹{cart.total} exceeds spending limit ₹{policy.max_transaction_amount}",
            total=cart.total,
            limit=policy.max_transaction_amount
        )
    
    return PolicyCheckResponse(
        allowed=True,
        reason="Policy check passed",
        total=cart.total,
        limit=policy.max_transaction_amount
    )

@router.post("/request-approval", response_model=ApprovalResponse)
async def request_approval(request: PaymentRequest, db: AsyncSession = Depends(get_db)):
    cart_result = await db.execute(select(Cart).where(Cart.id == request.cart_id))
    cart = cart_result.scalar_one_or_none()
    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")
    
    order = Order(
        cart_id=cart.id,
        customer_id=cart.customer_id,
        merchant_id="default",
        total=cart.total,
        status="approval_pending"
    )
    db.add(order)
    await db.commit()
    await db.refresh(order)
    
    token = str(uuid.uuid4())
    approval = Approval(
        order_id=order.id,
        session_id=request.session_id,
        status="pending",
        token=token
    )
    db.add(approval)
    await db.commit()
    await db.refresh(approval)
    
    await log_audit(db, request.session_id, "user", "request_approval", 
                    json.dumps({"cart_id": request.cart_id, "total": cart.total}),
                    "pending", "approval_requested")
    
    return ApprovalResponse(
        approval_id=approval.id,
        token=token,
        status="pending",
        message=f"Payment approval requested for ₹{cart.total}"
    )

@router.post("/approve/{approval_id}")
async def approve_payment(approval_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Approval).where(Approval.id == approval_id))
    approval = result.scalar_one_or_none()
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")
    
    approval.status = "approved"
    approval.approved_by = "user"
    
    order_result = await db.execute(select(Order).where(Order.id == approval.order_id))
    order = order_result.scalar_one_or_none()
    if order:
        order.status = "approved"
    
    await db.commit()
    
    await log_audit(db, approval.session_id, "user", "approve_payment",
                    json.dumps({"approval_id": approval_id}),
                    "approved", "payment_approved")
    
    return {"status": "approved", "order_id": approval.order_id}

async def log_audit(db: AsyncSession, session_id: str, user: str, action: str, 
                    input_data: str, decision: str, final_status: str):
    audit = AuditLog(
        session_id=session_id,
        user=user,
        action=action,
        input_data=input_data,
        decision=decision,
        final_status=final_status,
        created_at=datetime.now(timezone.utc)
    )
    db.add(audit)
    await db.commit()
