"""
Comprehensive tests for AI Growth and Commerce Agent backend.
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from httpx import AsyncClient, ASGITransport
from main import app
from models.database import engine, Base, async_session
from models.models import Product, Policy, Merchant, ProductRelationship, Order


@pytest.fixture(scope="session", autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as db:
        merchant = Merchant(id="test_merchant", name="Test Shop", email="test@test.com")
        db.add(merchant)

        products = [
            Product(id="p1", merchant_id="test_merchant", name="Wireless Headphones", category="Audio",
                    subcategory="Headphones", brand="Sony", price=2499, cost_price=1200, stock=10, sales=25,
                    revenue=62475, margin=51.98, description="Premium wireless headphones", sku="SKU-P1",
                    rating=4.5, currency="INR"),
            Product(id="p2", merchant_id="test_merchant", name="Headphone Case", category="Audio",
                    subcategory="Cases", brand="Generic", price=199, cost_price=50, stock=20, sales=40,
                    revenue=7960, margin=74.87, description="Protective case for headphones", sku="SKU-P2",
                    rating=4.0, currency="INR"),
            Product(id="p3", merchant_id="test_merchant", name="Laptop Backpack", category="Computer Accessories",
                    subcategory="Bags", brand="Wildcraft", price=1999, cost_price=800, stock=15, sales=15,
                    revenue=29985, margin=59.98, description="Water-resistant laptop backpack", sku="SKU-P3",
                    rating=4.2, currency="INR"),
            Product(id="p4", merchant_id="test_merchant", name="Out of Stock Item", category="Electronics",
                    subcategory="Other", brand="Generic", price=999, cost_price=400, stock=0, sales=5,
                    revenue=4995, margin=59.96, description="This item is out of stock", sku="SKU-P4",
                    rating=3.5, currency="INR"),
            Product(id="p5", merchant_id="test_merchant", name="Wireless Mouse", category="Computer Accessories",
                    subcategory="Mice", brand="Logitech", price=1299, cost_price=500, stock=30, sales=30,
                    revenue=38970, margin=61.51, description="Ergonomic wireless mouse", sku="SKU-P5",
                    rating=4.3, currency="INR"),
            Product(id="p6", merchant_id="test_merchant", name="Mechanical Keyboard", category="Computer Accessories",
                    subcategory="Keyboards", brand="Keychron", price=3499, cost_price=1800, stock=5, sales=8,
                    revenue=27992, margin=48.56, description="RGB mechanical keyboard", sku="SKU-P6",
                    rating=4.7, currency="INR"),
        ]
        for p in products:
            db.add(p)

        rels = [
            ProductRelationship(product_id="p1", related_product_id="p2", relationship_type="cross-sell", reason="Protect your headphones"),
            ProductRelationship(product_id="p1", related_product_id="p3", relationship_type="upsell", reason="Carry your gear"),
            ProductRelationship(product_id="p5", related_product_id="p3", relationship_type="cross-sell", reason="Complete your setup"),
        ]
        for r in rels:
            db.add(r)

        policy = Policy(max_transaction_amount=500000, payment_requires_approval=False)
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
    data = resp.json()
    assert data["status"] == "healthy"
    assert "ai" in data
    assert "razorpay" in data


# ==================== Products API ====================

async def test_products_list(client):
    resp = await client.get("/api/products/")
    assert resp.status_code == 200
    data = resp.json()
    assert "products" in data
    assert "total" in data
    assert data["total"] > 0
    assert data["page"] == 1
    assert len(data["products"]) > 0


async def test_products_pagination(client):
    resp = await client.get("/api/products/?page=1&page_size=3")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["products"]) <= 3
    assert data["page_size"] == 3


async def test_products_category_filter(client):
    resp = await client.get("/api/products/?category=Audio")
    assert resp.status_code == 200
    data = resp.json()
    for p in data["products"]:
        assert p["category"] == "Audio"


async def test_products_search(client):
    resp = await client.get("/api/products/?q=headphones")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] > 0


async def test_products_price_filter(client):
    resp = await client.get("/api/products/?max_price=500")
    assert resp.status_code == 200
    data = resp.json()
    for p in data["products"]:
        assert p["price"] <= 500


async def test_products_sort(client):
    resp = await client.get("/api/products/?sort_by=price&sort_order=desc&page_size=5")
    assert resp.status_code == 200
    data = resp.json()
    prices = [p["price"] for p in data["products"]]
    assert prices == sorted(prices, reverse=True)


async def test_products_categories(client):
    resp = await client.get("/api/products/categories")
    assert resp.status_code == 200
    cats = resp.json()
    assert len(cats) > 0
    assert "name" in cats[0]
    assert "count" in cats[0]


async def test_products_stats(client):
    resp = await client.get("/api/products/stats")
    assert resp.status_code == 200
    stats = resp.json()
    assert stats["total_products"] > 0
    assert "avg_price" in stats
    assert "total_revenue" in stats


async def test_product_by_id(client):
    resp = await client.get("/api/products/p1")
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Wireless Headphones"
    assert data["price"] == 2499
    assert data["cost_price"] == 1200


async def test_product_not_found(client):
    resp = await client.get("/api/products/nonexistent")
    assert resp.status_code == 404


async def test_product_update(client):
    resp = await client.put("/api/products/p1", json={"price": 2799, "stock": 12})
    assert resp.status_code == 200
    data = resp.json()
    assert data["price"] == 2799
    assert data["stock"] == 12
    # Restore
    await client.put("/api/products/p1", json={"price": 2499, "stock": 10})


async def test_agent_catalog(client):
    resp = await client.get("/api/products/agent/catalog")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) > 0
    for item in data:
        assert "product_id" in item
        assert "availability" in item


# ==================== Cart Operations ====================

async def test_cart_session_add(client):
    resp = await client.post("/api/carts/session/test_s1/add",
        json={"product_id": "p1", "quantity": 1})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2499
    assert data["item_count"] == 1


async def test_cart_session_get(client):
    resp = await client.get("/api/carts/session/test_s1")
    assert resp.status_code == 200
    data = resp.json()
    assert data["item_count"] >= 1


async def test_cart_session_quantity_update(client):
    resp = await client.patch("/api/carts/session/test_s1/item/p1",
        json={"quantity": 3})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 7497  # 2499 * 3


async def test_cart_session_remove(client):
    resp = await client.delete("/api/carts/session/test_s1/item/p1")
    assert resp.status_code == 200
    data = resp.json()
    assert data["item_count"] == 0


async def test_cart_session_clear(client):
    await client.post("/api/carts/session/test_s2/add", json={"product_id": "p1", "quantity": 1})
    resp = await client.delete("/api/carts/session/test_s2/clear")
    assert resp.status_code == 200
    assert resp.json()["item_count"] == 0


async def test_cart_stock_validation(client):
    resp = await client.post("/api/carts/session/test_stock/add",
        json={"product_id": "p4", "quantity": 1})
    assert resp.status_code == 400


async def test_cart_product_not_found(client):
    resp = await client.post("/api/carts/session/test_nf/add",
        json={"product_id": "nonexistent", "quantity": 1})
    assert resp.status_code == 404


# ==================== Checkout & Orders ====================

async def test_checkout(client):
    # Setup cart
    await client.post("/api/carts/session/test_checkout/add",
        json={"product_id": "p1", "quantity": 1})
    await client.post("/api/carts/session/test_checkout/add",
        json={"product_id": "p2", "quantity": 2})

    resp = await client.post("/api/orders/checkout", json={
        "session_id": "test_checkout",
        "customer_name": "Test User",
        "customer_email": "test@example.com",
        "customer_phone": "+919876543210",
        "customer_address": "123 Test Street",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "pending"
    assert data["customer_name"] == "Test User"
    assert data["total"] > 0
    assert data["tax"] > 0
    assert len(data["items"]) >= 2


async def test_checkout_empty_cart(client):
    resp = await client.post("/api/orders/checkout", json={
        "session_id": "nonexistent_session",
        "customer_name": "Test",
        "customer_email": "test@test.com",
    })
    assert resp.status_code == 404


async def test_orders_list(client):
    resp = await client.get("/api/orders/")
    assert resp.status_code == 200
    data = resp.json()
    assert "orders" in data
    assert "total" in data


async def test_orders_stats(client):
    resp = await client.get("/api/orders/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert "total_orders" in data
    assert "total_revenue" in data


# ==================== Payment ====================

async def test_create_razorpay_order(client):
    # First create an order via checkout
    await client.post("/api/carts/session/test_pay/add",
        json={"product_id": "p1", "quantity": 1})
    checkout_resp = await client.post("/api/orders/checkout", json={
        "session_id": "test_pay",
        "customer_name": "Pay Test",
        "customer_email": "pay@test.com",
    })
    order_id = checkout_resp.json()["id"]

    resp = await client.post("/api/payments/create-order", json={"order_id": order_id})
    assert resp.status_code == 200
    data = resp.json()
    assert "razorpay_order_id" in data
    assert data["amount"] > 0


async def test_demo_payment_success(client):
    # Create an order
    await client.post("/api/carts/session/test_demo_s/add",
        json={"product_id": "p2", "quantity": 1})
    checkout_resp = await client.post("/api/orders/checkout", json={
        "session_id": "test_demo_s",
        "customer_name": "Demo Test",
        "customer_email": "demo@test.com",
    })
    order_id = checkout_resp.json()["id"]

    resp = await client.post(f"/api/payments/demo-success/{order_id}")
    assert resp.status_code == 200
    assert resp.json()["status"] == "success"


async def test_payment_list(client):
    resp = await client.get("/api/payments/")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


# ==================== Pricing ====================

async def test_pricing_recommendation(client):
    resp = await client.get("/api/pricing/recommend/p1")
    assert resp.status_code == 200
    data = resp.json()
    assert data["product_id"] == "p1"
    assert data["current_price"] > 0
    assert data["recommended_price"] > 0
    assert "confidence" in data
    assert "explanation" in data


async def test_pricing_not_found(client):
    resp = await client.get("/api/pricing/recommend/nonexistent")
    assert resp.status_code == 404


async def test_apply_price(client):
    resp = await client.post("/api/pricing/apply",
        json={"product_id": "p1", "new_price": 2599})
    assert resp.status_code == 200
    assert resp.json()["status"] == "success"
    # Restore
    await client.post("/api/pricing/apply",
        json={"product_id": "p1", "new_price": 2499})


# ==================== Notifications ====================

async def test_notifications_list(client):
    resp = await client.get("/api/notifications/")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


async def test_notifications_unread_count(client):
    resp = await client.get("/api/notifications/unread-count")
    assert resp.status_code == 200
    assert "count" in resp.json()


# ==================== Audit Trail ====================

async def test_audit_list(client):
    resp = await client.get("/api/audit/")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


async def test_audit_filter(client):
    resp = await client.get("/api/audit/?event_type=payment")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


# ==================== Analytics ====================

async def test_analytics(client):
    resp = await client.get("/api/analytics/")
    assert resp.status_code == 200
    data = resp.json()
    assert "total_orders" in data
    assert "total_revenue" in data
    assert "total_products" in data


async def test_dashboard(client):
    resp = await client.get("/api/analytics/dashboard")
    assert resp.status_code == 200
    data = resp.json()
    assert "revenue_chart" in data
    assert "top_products" in data
    assert "recent_orders" in data
    assert isinstance(data["revenue_chart"], list)


async def test_revenue_chart(client):
    resp = await client.get("/api/analytics/revenue-chart?period=7d")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) > 0


# ==================== Policies ====================

async def test_get_policy(client):
    resp = await client.get("/api/policies/")
    assert resp.status_code == 200
    data = resp.json()
    assert "max_transaction_amount" in data


async def test_update_policy(client):
    resp = await client.put("/api/policies/", json={"max_transaction_amount": 99999})
    assert resp.status_code == 200
    assert resp.json()["max_transaction_amount"] == 99999
    # Restore
    await client.put("/api/policies/", json={"max_transaction_amount": 500000})


# ==================== Full E2E Flow ====================

async def test_e2e_cart_to_payment(client):
    """Test the full flow: add to cart -> checkout -> payment -> success."""
    # 1. Add items to cart
    add_resp = await client.post("/api/carts/session/e2e_test/add",
        json={"product_id": "p1", "quantity": 1})
    assert add_resp.status_code == 200

    add_resp2 = await client.post("/api/carts/session/e2e_test/add",
        json={"product_id": "p2", "quantity": 1})
    assert add_resp2.status_code == 200

    # 2. Get cart
    cart_resp = await client.get("/api/carts/session/e2e_test")
    assert cart_resp.status_code == 200
    cart = cart_resp.json()
    assert cart["item_count"] == 2

    # 3. Checkout
    checkout_resp = await client.post("/api/orders/checkout", json={
        "session_id": "e2e_test",
        "customer_name": "E2E Customer",
        "customer_email": "e2e@test.com",
    })
    assert checkout_resp.status_code == 200
    order = checkout_resp.json()
    assert order["status"] == "pending"
    assert order["tax"] > 0

    # 4. Demo payment
    pay_resp = await client.post(f"/api/payments/demo-success/{order['id']}")
    assert pay_resp.status_code == 200

    # 5. Verify order updated
    order_resp = await client.get(f"/api/orders/{order['id']}")
    assert order_resp.status_code == 200
    assert order_resp.json()["status"] == "success"

    # 6. Verify audit trail
    audit_resp = await client.get("/api/audit/")
    assert audit_resp.status_code == 200
    # Should have payment success audit event
