import pytest
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from httpx import AsyncClient, ASGITransport
from main import app
from models.database import engine, Base, async_session
from models.models import Product, Policy, Merchant

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session", autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with async_session() as db:
        merchant = Merchant(id="test_merchant", name="Test Shop", email="test@test.com")
        db.add(merchant)
        products = [
            Product(id="p1", merchant_id="test_merchant", name="Headphones", category="Audio", price=2499, stock=10),
            Product(id="p2", merchant_id="test_merchant", name="Case", category="Audio", price=199, stock=20),
            Product(id="p3", merchant_id="test_merchant", name="Laptop", category="Electronics", price=45000, stock=5),
            Product(id="p4", merchant_id="test_merchant", name="Out of Stock", category="Electronics", price=999, stock=0),
        ]
        for p in products:
            db.add(p)
        policy = Policy(merchant_id="test_merchant", max_transaction_amount=3000, payment_requires_approval=True)
        db.add(policy)
        await db.commit()

@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

@pytest.mark.asyncio
async def test_search_products(client):
    resp = await client.post("/api/agent/search", json={"query": "headphones", "session_id": "test"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["products"]) > 0
    assert data["products"][0]["name"] == "Headphones"

@pytest.mark.asyncio
async def test_search_with_price_limit(client):
    resp = await client.post("/api/agent/search", json={"query": "headphones", "max_price": 3000, "session_id": "test"})
    assert resp.status_code == 200
    data = resp.json()
    for p in data["products"]:
        assert p["price"] <= 3000

@pytest.mark.asyncio
async def test_cart_total_calculation(client):
    resp = await client.post("/api/agent/cart", json={"product_ids": ["p1", "p2"], "session_id": "test"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2698.0

@pytest.mark.asyncio
async def test_inventory_validation(client):
    resp = await client.post("/api/agent/cart", json={"product_ids": ["p4"], "session_id": "test"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 0

@pytest.mark.asyncio
async def test_policy_block(client):
    resp = await client.post("/api/agent/policy-check", json={"cart_id": "nonexistent", "session_id": "test"})
    assert resp.status_code == 404

@pytest.mark.asyncio
async def test_approval_required(client):
    cart_resp = await client.post("/api/agent/cart", json={"product_ids": ["p1"], "session_id": "test"})
    cart_id = cart_resp.json()["cart_id"]
    resp = await client.post("/api/agent/request-approval", json={"cart_id": cart_id, "session_id": "test"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "pending"

@pytest.mark.asyncio
async def test_duplicate_payment_prevention(client):
    pass

@pytest.mark.asyncio
async def test_invalid_product(client):
    resp = await client.post("/api/agent/cart", json={"product_ids": ["invalid"], "session_id": "test"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 0

@pytest.mark.asyncio
async def test_audit_logging(client):
    resp = await client.get("/api/audit/")
    assert resp.status_code == 200
