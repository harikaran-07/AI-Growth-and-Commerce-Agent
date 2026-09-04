from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Text, Boolean, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid
from models.database import Base

def gen_uuid():
    return str(uuid.uuid4())

def utcnow():
    return datetime.now(timezone.utc)

class Merchant(Base):
    __tablename__ = "merchants"
    id = Column(String, primary_key=True, default=gen_uuid)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime, default=utcnow)
    products = relationship("Product", back_populates="merchant")
    policies = relationship("Policy", back_populates="merchant")

class Product(Base):
    __tablename__ = "products"
    id = Column(String, primary_key=True, default=gen_uuid)
    merchant_id = Column(String, ForeignKey("merchants.id"))
    name = Column(String, nullable=False)
    description = Column(Text)
    category = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    previous_price = Column(Float)
    cost_price = Column(Float)
    currency = Column(String, default="INR")
    subcategory = Column(String)
    brand = Column(String)
    sku = Column(String, unique=True)
    rating = Column(Float, default=0.0)
    tags = Column(Text)
    stock = Column(Integer, default=0)
    sales = Column(Integer, default=0)
    revenue = Column(Float, default=0.0)
    margin = Column(Float, default=0.0)
    image_url = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)
    merchant = relationship("Merchant", back_populates="products")
    relationships = relationship("ProductRelationship", foreign_keys="ProductRelationship.product_id", back_populates="product")

class ProductRelationship(Base):
    __tablename__ = "product_relationships"
    id = Column(String, primary_key=True, default=gen_uuid)
    product_id = Column(String, ForeignKey("products.id"))
    related_product_id = Column(String, ForeignKey("products.id"))
    relationship_type = Column(String)
    reason = Column(Text)
    product = relationship("Product", foreign_keys=[product_id], back_populates="relationships")
    related_product = relationship("Product", foreign_keys=[related_product_id])

class Customer(Base):
    __tablename__ = "customers"
    id = Column(String, primary_key=True, default=gen_uuid)
    name = Column(String)
    email = Column(String)
    session_id = Column(String, unique=True)
    created_at = Column(DateTime, default=utcnow)

class Cart(Base):
    __tablename__ = "carts"
    id = Column(String, primary_key=True, default=gen_uuid)
    customer_id = Column(String, ForeignKey("customers.id"))
    session_id = Column(String)
    status = Column(String, default="active")
    total = Column(Float, default=0)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)
    items = relationship("CartItem", back_populates="cart")

class CartItem(Base):
    __tablename__ = "cart_items"
    id = Column(String, primary_key=True, default=gen_uuid)
    cart_id = Column(String, ForeignKey("carts.id"))
    product_id = Column(String, ForeignKey("products.id"))
    quantity = Column(Integer, default=1)
    price_at_time = Column(Float)
    cart = relationship("Cart", back_populates="items")
    product = relationship("Product")

class Order(Base):
    __tablename__ = "orders"
    id = Column(String, primary_key=True, default=gen_uuid)
    cart_id = Column(String, ForeignKey("carts.id"))
    customer_id = Column(String, ForeignKey("customers.id"))
    merchant_id = Column(String, ForeignKey("merchants.id"))
    customer_name = Column(String)
    customer_email = Column(String)
    customer_phone = Column(String)
    customer_address = Column(Text)
    subtotal = Column(Float, default=0)
    discount = Column(Float, default=0)
    tax = Column(Float, default=0)
    shipping = Column(Float, default=0)
    total = Column(Float, nullable=False)
    status = Column(String, default="PENDING_PAYMENT")
    payment_status = Column(String, default="PENDING")
    razorpay_order_id = Column(String)
    razorpay_payment_id = Column(String)
    notes = Column(Text)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)
    cart = relationship("Cart")
    payment = relationship("Payment", back_populates="order", uselist=False)
    items = relationship("OrderItem", back_populates="order")

class OrderItem(Base):
    __tablename__ = "order_items"
    id = Column(String, primary_key=True, default=gen_uuid)
    order_id = Column(String, ForeignKey("orders.id"))
    product_id = Column(String, ForeignKey("products.id"))
    product_name = Column(String)
    quantity = Column(Integer, default=1)
    price = Column(Float)
    subtotal = Column(Float)
    order = relationship("Order", back_populates="items")
    product = relationship("Product")

class Payment(Base):
    __tablename__ = "payments"
    id = Column(String, primary_key=True, default=gen_uuid)
    order_id = Column(String, ForeignKey("orders.id"))
    amount = Column(Float, nullable=False)
    currency = Column(String, default="INR")
    status = Column(String, default="CREATED")
    razorpay_order_id = Column(String)
    razorpay_payment_id = Column(String)
    razorpay_signature = Column(String)
    failure_reason = Column(Text)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)
    order = relationship("Order", back_populates="payment")

class Policy(Base):
    __tablename__ = "policies"
    id = Column(String, primary_key=True, default=gen_uuid)
    merchant_id = Column(String, ForeignKey("merchants.id"))
    max_transaction_amount = Column(Float, default=500000)
    max_discount_percentage = Column(Float, default=10)
    payment_requires_approval = Column(Boolean, default=False)
    max_retry_attempts = Column(Integer, default=1)
    # Campaign safety limits (money-action boundaries for the orchestrator)
    max_campaign_budget = Column(Float, default=100000)
    minimum_margin_percentage = Column(Float, default=20)
    created_at = Column(DateTime, default=utcnow)
    merchant = relationship("Merchant", back_populates="policies")


class Campaign(Base):
    """A merchant-approved promotional campaign (synthetic demo execution).

    Lifecycle: proposed → pending_approval → approved → executing → completed
    (or proposed → rejected_by_policy / approved → rejected).
    """
    __tablename__ = "campaigns"
    id = Column(String, primary_key=True, default=gen_uuid)
    name = Column(String, nullable=False)
    objective = Column(String)
    target_segment = Column(String)
    product_ids = Column(Text, default="[]")   # JSON list
    discount_percentage = Column(Float, default=0)
    budget_limit = Column(Float, default=0)
    expected_revenue = Column(Float, default=0)
    expected_profit = Column(Float, default=0)
    expected_margin = Column(Float, default=0)
    reason = Column(Text)
    evidence = Column(Text)
    status = Column(String, default="proposed")
    policy_result = Column(String)              # pass / blocked reason
    approval_status = Column(String, default="none")  # none|pending|approved|rejected
    result = Column(Text)                        # JSON simulation result (synthetic)
    failure_reason = Column(Text)
    label = Column(String, default="Synthetic Demo Result")
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)
    executed_at = Column(DateTime)

class Approval(Base):
    __tablename__ = "approvals"
    id = Column(String, primary_key=True, default=gen_uuid)
    order_id = Column(String, ForeignKey("orders.id"))
    session_id = Column(String)
    status = Column(String, default="pending")
    approved_by = Column(String)
    token = Column(String)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(String, primary_key=True, default=gen_uuid)
    session_id = Column(String)
    user = Column(String)
    action = Column(String, nullable=False)
    description = Column(Text)
    tool_called = Column(String)
    input_data = Column(Text)
    decision = Column(String)
    policy_result = Column(String)
    approval_status = Column(String)
    payment_reference = Column(String)
    final_status = Column(String)
    event_type = Column(String, default="system")
    related_entity = Column(String)
    financial_impact = Column(Float)
    created_at = Column(DateTime, default=utcnow)

class AgentSession(Base):
    __tablename__ = "agent_sessions"
    id = Column(String, primary_key=True, default=gen_uuid)
    customer_id = Column(String, ForeignKey("customers.id"))
    status = Column(String, default="active")
    messages = Column(Text, default="[]")
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

class Notification(Base):
    __tablename__ = "notifications"
    id = Column(String, primary_key=True, default=gen_uuid)
    title = Column(String, nullable=False)
    message = Column(Text)
    type = Column(String, default="info")
    is_read = Column(Boolean, default=False)
    related_entity = Column(String)
    created_at = Column(DateTime, default=utcnow)
