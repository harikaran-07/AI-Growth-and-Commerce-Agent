"""
Comprehensive tests for MerchantFlow AI backend.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from httpx import AsyncClient, ASGITransport
from main import app
from models.database import engine, Base, async_session
from models.models import Product, Policy, Merchant, ProductRelationship


@pytest.fixture(scope="session", autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as db:
        merchant = Merchant(id="test_merchant", name="Test Shop", email="test@test.com")
        db.add(merchant)

        products = [
            Product(id="p1", merchant_id="test_merchant", name="Wireless Headphones", category="Audio", price=2499, stock=10, description="Premium wireless headphones"),
            Product(id="p2", merchant_id="test_merchant", name="Headphone Case", category="Audio", price=199, stock=20, description="Protective case for headphones"),
            Product(id="p3", merchant_id="test_merchant", name="Laptop Backpack", category="Computer Accessories", price=1999, stock=15, description="Water-resistant laptop backpack"),
            Product(id="p4", merchant_id="test_merchant", name="Out of Stock Item", category="Electronics", price=999, stock=0, description="This item is out of stock"),
            Product(id="p5", merchant_id="test_merchant", name="Wireless Mouse", category="Computer Accessories", price=1299, stock=30, description="Ergonomic wireless mouse"),
            Product(id="p6", merchant_id="test_merchant", name="Mechanical Keyboard", category="Computer Accessories", price=3499, stock=5, description="RGB mechanical keyboard"),
        ]
        for p in products:
            db.add(p)

        rels = [
            ProductRelationship(product_id="p1", related_product_id="p2", relationship_type="cross-sell", reason="Protect your headphones"),
            ProductRelationship(product_id="p1", related_product_id="p3", relationship_type="complementary", reason="Carry your gear"),
            ProductRelationship(product_id="p5", related_product_id="p3", relationship_type="cross-sell", reason="Complete your setup"),
        ]
        for r in rels:
            db.add(r)

        policy = Policy(merchant_id="test_merchant", max_transaction_amount=3000, payment_requires_approval=True, max_retry_attempts=1)
        db.add(policy)
        await db.commit()


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ==================== Health & Root ====================

async def test_health(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"


async def test_root(client):  # noqa: F811
    resp = await client.get("/")
    assert resp.status_code == 200
    assert resp.status_code == 200


# ==================== Product Search ====================

async def test_search_products(client):
    resp = await client.post("/api/agent/search", json={"query": "headphones", "session_id": "test_search"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["products"]) > 0
    names = [p["name"] for p in data["products"]]
    assert any("Headphones" in name for name in names)


async def test_search_with_price_limit(client):
    resp = await client.post("/api/agent/search", json={"query": "", "max_price": 500, "session_id": "test_price"})
    assert resp.status_code == 200
    data = resp.json()
    for p in data["products"]:
        assert p["price"] <= 500


async def test_search_out_of_stock_excluded(client):
    resp = await client.post("/api/agent/search", json={"query": "", "session_id": "test_stock"})
    assert resp.status_code == 200
    data = resp.json()
    for p in data["products"]:
        assert p["stock"] > 0


# ==================== Recommendations ====================

async def test_recommendations_from_catalog(client):
    resp = await client.post("/api/agent/search", json={"query": "headphones", "session_id": "test_rec"})
    assert resp.status_code == 200
    data = resp.json()
    if data["recommendations"]:
        for rec in data["recommendations"]:
            assert "product_id" in rec
            assert "name" in rec
            assert "price" in rec
            assert "reason" in rec


# ==================== Cart Operations ====================

async def test_cart_creation_and_total(client):
    resp = await client.post("/api/agent/cart", json={"product_ids": ["p1", "p2"], "session_id": "test_cart"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2698.0
    assert len(data["items"]) == 2


async def test_cart_inventory_validation(client):
    resp = await client.post("/api/agent/cart", json={"product_ids": ["p4"], "session_id": "test_cart_inv"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 0


async def test_cart_invalid_product(client):
    resp = await client.post("/api/agent/cart", json={"product_ids": ["invalid_id"], "session_id": "test_cart_inv2"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 0


async def test_cart_item_quantity_validation(client):
    cart_resp = await client.post("/api/carts/", params={"session_id": "test_qty"})
    cart_id = cart_resp.json()["id"]
    resp = await client.post(f"/api/carts/{cart_id}/items", json={"product_id": "p1", "quantity": 0})
    assert resp.status_code == 422


async def test_cart_get_endpoint(client):
    create_resp = await client.post("/api/agent/cart", json={"product_ids": ["p1", "p5"], "session_id": "test_get_cart"})
    cart_id = create_resp.json()["cart_id"]
    resp = await client.get(f"/api/carts/{cart_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "active"
    assert len(data["items"]) == 2
    assert data["total"] == 2499 + 1299


# ==================== Policy Check ====================

async def test_policy_within_limit(client):
    create_resp = await client.post("/api/agent/cart", json={"product_ids": ["p1", "p2"], "session_id": "test_policy_ok"})
    cart_id = create_resp.json()["cart_id"]
    resp = await client.post("/api/agent/policy-check", json={"cart_id": cart_id, "session_id": "test_policy_ok"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["allowed"] is True
    assert data["total"] == 2698


async def test_policy_nonexistent_cart(client):
    resp = await client.post("/api/agent/policy-check", json={"cart_id": "nonexistent", "session_id": "test"})
    assert resp.status_code == 404


# ==================== Approval ====================

async def test_approval_required(client):
    cart_resp = await client.post("/api/agent/cart", json={"product_ids": ["p1"], "session_id": "test_approval"})
    cart_id = cart_resp.json()["cart_id"]
    resp = await client.post("/api/agent/request-approval", json={"cart_id": cart_id, "session_id": "test_approval"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "pending"
    assert data["approval_id"]


async def test_approve_and_reject(client):
    cart_resp = await client.post("/api/agent/cart", json={"product_ids": ["p2"], "session_id": "test_approve_reject"})
    cart_id = cart_resp.json()["cart_id"]
    approval_resp = await client.post("/api/agent/request-approval", json={"cart_id": cart_id, "session_id": "test_approve_reject"})
    approval_id = approval_resp.json()["approval_id"]
    approve_resp = await client.post(f"/api/approvals/{approval_id}/approve")
    assert approve_resp.status_code == 200
    assert approve_resp.json()["status"] == "approved"
    approve_again = await client.post(f"/api/approvals/{approval_id}/approve")
    assert approve_again.status_code == 400


async def test_approval_already_processed(client):
    cart_resp = await client.post("/api/agent/cart", json={"product_ids": ["p2"], "session_id": "test_already_proc"})
    cart_id = cart_resp.json()["cart_id"]
    approval_resp = await client.post("/api/agent/request-approval", json={"cart_id": cart_id, "session_id": "test_already_proc"})
    approval_id = approval_resp.json()["approval_id"]
    await client.post(f"/api/approvals/{approval_id}/approve")
    resp = await client.post(f"/api/approvals/{approval_id}/approve")
    assert resp.status_code == 400


# ==================== Payment ====================

async def test_payment_without_approval_blocked(client):
    cart_resp = await client.post("/api/agent/cart", json={"product_ids": ["p1"], "session_id": "test_pay_auth"})
    cart_id = cart_resp.json()["cart_id"]
    approval_resp = await client.post("/api/agent/request-approval", json={"cart_id": cart_id, "session_id": "test_pay_auth"})
    order_id = approval_resp.json()["order_id"]
    resp = await client.post("/api/payments/", json={"order_id": order_id})
    assert resp.status_code == 400


async def test_payment_with_approval(client):
    cart_resp = await client.post("/api/agent/cart", json={"product_ids": ["p2"], "session_id": "test_pay_ok"})
    cart_id = cart_resp.json()["cart_id"]
    approval_resp = await client.post("/api/agent/request-approval", json={"cart_id": cart_id, "session_id": "test_pay_ok"})
    approval_id = approval_resp.json()["approval_id"]
    order_id = approval_resp.json()["order_id"]
    await client.post(f"/api/approvals/{approval_id}/approve")
    resp = await client.post("/api/payments/", json={"order_id": order_id})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "initiated"


async def test_payment_nonexistent_order(client):
    resp = await client.post("/api/payments/", json={"order_id": "nonexistent"})
    assert resp.status_code == 404


async def test_payment_list_endpoint(client):
    resp = await client.get("/api/payments/")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


# ==================== Duplicate Payment Prevention ====================

async def test_duplicate_payment_prevention(client):
    cart_resp = await client.post("/api/agent/cart", json={"product_ids": ["p2"], "session_id": "test_dup"})
    cart_id = cart_resp.json()["cart_id"]
    approval_resp = await client.post("/api/agent/request-approval", json={"cart_id": cart_id, "session_id": "test_dup"})
    approval_id = approval_resp.json()["approval_id"]
    order_id = approval_resp.json()["order_id"]
    await client.post(f"/api/approvals/{approval_id}/approve")
    pay1 = await client.post("/api/payments/", json={"order_id": order_id})
    assert pay1.status_code == 200
    payment_id = pay1.json()["id"]
    await client.post(f"/api/payments/demo-fail/{payment_id}")
    pay2 = await client.post("/api/payments/", json={"order_id": order_id})
    assert pay2.status_code == 400


async def test_no_payment_while_initiated(client):
    cart_resp = await client.post("/api/agent/cart", json={"product_ids": ["p2"], "session_id": "test_no_dup2"})
    cart_id = cart_resp.json()["cart_id"]
    approval_resp = await client.post("/api/agent/request-approval", json={"cart_id": cart_id, "session_id": "test_no_dup2"})
    approval_id = approval_resp.json()["approval_id"]
    order_id = approval_resp.json()["order_id"]
    await client.post(f"/api/approvals/{approval_id}/approve")
    pay1 = await client.post("/api/payments/", json={"order_id": order_id})
    assert pay1.status_code == 200
    pay2 = await client.post("/api/payments/", json={"order_id": order_id})
    assert pay2.status_code in (400, 409)


# ==================== Webhook Idempotency ====================

async def test_webhook_idempotency(client):
    cart_resp = await client.post("/api/agent/cart", json={"product_ids": ["p2"], "session_id": "test_webhook"})
    cart_id = cart_resp.json()["cart_id"]
    approval_resp = await client.post("/api/agent/request-approval", json={"cart_id": cart_id, "session_id": "test_webhook"})
    approval_id = approval_resp.json()["approval_id"]
    order_id = approval_resp.json()["order_id"]
    await client.post(f"/api/approvals/{approval_id}/approve")
    pay_resp = await client.post("/api/payments/", json={"order_id": order_id})
    razorpay_order_id = pay_resp.json()["razorpay_order_id"]
    webhook_payload = {
        "event": "payment.captured",
        "payload": {"payment": {"entity": {"id": "pay_test_123", "order_id": razorpay_order_id}}}
    }
    resp1 = await client.post("/api/webhooks/razorpay", json=webhook_payload)
    assert resp1.status_code == 200
    resp2 = await client.post("/api/webhooks/razorpay", json=webhook_payload)
    assert resp2.status_code == 200
    pay_check = await client.get(f"/api/payments/{pay_resp.json()['id']}")
    assert pay_check.json()["status"] == "success"


# ==================== Audit ====================

async def test_audit_logging(client):
    await client.post("/api/agent/search", json={"query": "headphones", "session_id": "test_audit"})
    resp = await client.get("/api/audit/")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


# ==================== Products API ====================

async def test_products_list(client):
    resp = await client.get("/api/products/")
    assert resp.status_code == 200
    assert len(resp.json()) > 0


async def test_products_category_filter(client):
    resp = await client.get("/api/products/?category=Audio")
    assert resp.status_code == 200
    for p in resp.json():
        assert p["category"] == "Audio"


async def test_agent_catalog(client):
    resp = await client.get("/api/products/agent/catalog")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) > 0
    for item in data:
        assert "product_id" in item
        assert "availability" in item


async def test_product_not_found(client):
    resp = await client.get("/api/products/nonexistent")
    assert resp.status_code == 404


# ==================== Policy API ====================

async def test_get_policy(client):
    resp = await client.get("/api/policies/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["max_transaction_amount"] > 0


async def test_update_policy(client):
    resp = await client.put("/api/policies/", json={"max_transaction_amount": 5000})
    assert resp.status_code == 200
    assert resp.json()["max_transaction_amount"] == 5000
    await client.put("/api/policies/", json={"max_transaction_amount": 3000})


# ==================== Demo Failure ====================

async def test_demo_payment_failure(client):
    cart_resp = await client.post("/api/agent/cart", json={"product_ids": ["p2"], "session_id": "test_demo_fail"})
    cart_id = cart_resp.json()["cart_id"]
    approval_resp = await client.post("/api/agent/request-approval", json={"cart_id": cart_id, "session_id": "test_demo_fail"})
    approval_id = approval_resp.json()["approval_id"]
    await client.post(f"/api/approvals/{approval_id}/approve")
    pay_resp = await client.post("/api/payments/", json={"order_id": approval_resp.json()["order_id"]})
    fail_resp = await client.post(f"/api/payments/demo-fail/{pay_resp.json()['id']}")
    assert fail_resp.status_code == 200
    assert fail_resp.json()["status"] == "failed"
    assert "DEMO" in fail_resp.json()["failure_reason"]


# ==================== Analytics ====================

async def test_analytics(client):
    resp = await client.get("/api/analytics/")
    assert resp.status_code == 200
    data = resp.json()
    assert "total_orders" in data
    assert "total_revenue" in data
