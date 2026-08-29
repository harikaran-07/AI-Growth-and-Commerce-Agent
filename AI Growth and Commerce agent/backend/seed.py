import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models.database import engine, Base, async_session
from models.models import Merchant, Product, ProductRelationship, Policy
import uuid

async def seed():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with async_session() as db:
        merchant = Merchant(
            id="merchant_001",
            name="TechZone Electronics",
            email="admin@techzone.in"
        )
        db.add(merchant)
        
        policy = Policy(
            merchant_id="merchant_001",
            max_transaction_amount=3000,
            max_discount_percentage=10,
            payment_requires_approval=True,
            max_retry_attempts=1
        )
        db.add(policy)
        
        products = [
            Product(id="prod_001", merchant_id="merchant_001", name="Wireless Bluetooth Headphones", description="Premium noise-cancelling wireless headphones with 30-hour battery life", category="Audio", price=2499, stock=50),
            Product(id="prod_002", merchant_id="merchant_001", name="Headphone Carrying Case", description="Hard shell protective case for headphones", category="Audio Accessories", price=199, stock=100),
            Product(id="prod_003", merchant_id="merchant_001", name="USB-C to 3.5mm Adapter", description="High-quality audio adapter for devices without headphone jack", category="Audio Accessories", price=299, stock=75),
            Product(id="prod_004", merchant_id="merchant_001", name="Wireless Gaming Mouse", description="Ergonomic wireless mouse with RGB lighting and 16000 DPI", category="Computer Accessories", price=1299, stock=40),
            Product(id="prod_005", merchant_id="merchant_001", name="Mouse Pad XL", description="Extended gaming mouse pad with anti-slip base", category="Computer Accessories", price=499, stock=60),
            Product(id="prod_006", merchant_id="merchant_001", name="Mechanical Keyboard", description="RGB mechanical keyboard with Cherry MX switches", category="Computer Accessories", price=3499, stock=25),
            Product(id="prod_007", merchant_id="merchant_001", name="Laptop Stand", description="Adjustable aluminum laptop stand for ergonomic viewing", category="Computer Accessories", price=899, stock=35),
            Product(id="prod_008", merchant_id="merchant_001", name="Wireless Keyboard", description="Slim wireless keyboard with quiet keys", category="Computer Accessories", price=1599, stock=30),
            Product(id="prod_009", merchant_id="merchant_001", name="USB-C Hub 7-in-1", description="Multi-port adapter with HDMI, USB-A, SD card reader", category="Computer Accessories", price=1999, stock=45),
            Product(id="prod_010", merchant_id="merchant_001", name="Webcam HD 1080p", description="Full HD webcam with built-in microphone", category="Computer Accessories", price=2199, stock=20),
            Product(id="prod_011", merchant_id="merchant_001", name="Screen Protector Tempered Glass", description="9H hardness tempered glass screen protector", category="Mobile Accessories", price=199, stock=200),
            Product(id="prod_012", merchant_id="merchant_001", name="Phone Case Clear", description="Crystal clear protective phone case", category="Mobile Accessories", price=299, stock=150),
            Product(id="prod_013", merchant_id="merchant_001", name="Wireless Phone Charger", description="15W fast wireless charging pad", category="Mobile Accessories", price=799, stock=80),
            Product(id="prod_014", merchant_id="merchant_001", name="Car Phone Mount", description="Dashboard magnetic phone holder", category="Mobile Accessories", price=399, stock=60),
            Product(id="prod_015", merchant_id="merchant_001", name="Portable Power Bank 10000mAh", description="Slim power bank with dual USB output", category="Mobile Accessories", price=999, stock=70),
            Product(id="prod_016", merchant_id="merchant_001", name="Smart LED Desk Lamp", description="Adjustable LED desk lamp with color temperature control", category="Office Products", price=1299, stock=40),
            Product(id="prod_017", merchant_id="merchant_001", name="Wireless Presentation Clicker", description="Laser pointer with wireless USB receiver", category="Office Products", price=599, stock=30),
            Product(id="prod_018", merchant_id="merchant_001", name="Monitor Stand Riser", description="Adjustable monitor stand with USB hub", category="Office Products", price=1499, stock=25),
            Product(id="prod_019", merchant_id="merchant_001", name="Desk Organizer", description="Multi-compartment desk organizer for stationery", category="Office Products", price=699, stock=45),
            Product(id="prod_020", merchant_id="merchant_001", name="Webcam Light Ring", description="Adjustable ring light for video calls", category="Office Products", price=899, stock=35),
            Product(id="prod_021", merchant_id="merchant_001", name="Bluetooth Speaker", description="Portable waterproof Bluetooth speaker", category="Audio", price=1799, stock=30),
            Product(id="prod_022", merchant_id="merchant_001", name="Speaker Mount", description="Wall mount bracket for speakers", category="Audio Accessories", price=349, stock=50),
            Product(id="prod_023", merchant_id="merchant_001", name="External SSD 500GB", description="Portable USB-C SSD with 500GB storage", category="Electronics", price=3999, stock=15),
            Product(id="prod_024", merchant_id="merchant_001", name="USB Flash Drive 64GB", description="Metal USB 3.0 flash drive", category="Electronics", price=499, stock=100),
            Product(id="prod_025", merchant_id="merchant_001", name="HDMI Cable 2m", description="4K HDMI cable with gold-plated connectors", category="Electronics", price=399, stock=80),
            Product(id="prod_026", merchant_id="merchant_001", name="Ethernet Cable Cat6", description="1m Cat6 Ethernet cable", category="Electronics", price=199, stock=120),
            Product(id="prod_027", merchant_id="merchant_001", name="Wireless Earbuds", description="True wireless earbuds with charging case", category="Audio", price=1499, stock=45),
            Product(id="prod_028", merchant_id="merchant_001", name="Earbuds Tips Replacement", description="Silicone ear tips in multiple sizes", category="Audio Accessories", price=149, stock=200),
            Product(id="prod_029", merchant_id="merchant_001", name="Laptop Cooling Pad", description="Dual fan laptop cooling pad", category="Computer Accessories", price=999, stock=30),
            Product(id="prod_030", merchant_id="merchant_001", name="Cable Management Kit", description="Velcro ties and cable clips for desk organization", category="Office Products", price=299, stock=150),
        ]
        
        for p in products:
            db.add(p)
        
        relationships = [
            ProductRelationship(product_id="prod_001", related_product_id="prod_002", relationship_type="cross-sell", reason="Protective case for your headphones"),
            ProductRelationship(product_id="prod_001", related_product_id="prod_003", relationship_type="complementary", reason="Connect to devices without headphone jack"),
            ProductRelationship(product_id="prod_004", related_product_id="prod_005", relationship_type="cross-sell", reason="Perfect surface for your gaming mouse"),
            ProductRelationship(product_id="prod_006", related_product_id="prod_004", relationship_type="upsell", reason="Complete your desktop setup"),
            ProductRelationship(product_id="prod_006", related_product_id="prod_007", relationship_type="complementary", reason="Ergonomic viewing for your laptop"),
            ProductRelationship(product_id="prod_008", related_product_id="prod_004", relationship_type="cross-sell", reason="Wireless keyboard pairs with wireless mouse"),
            ProductRelationship(product_id="prod_011", related_product_id="prod_012", relationship_type="cross-sell", reason="Complete phone protection"),
            ProductRelationship(product_id="prod_012", related_product_id="prod_013", relationship_type="complementary", reason="Charge your phone while protected"),
            ProductRelationship(product_id="prod_013", related_product_id="prod_015", relationship_type="upsell", reason="Charge on the go"),
            ProductRelationship(product_id="prod_016", related_product_id="prod_019", relationship_type="cross-sell", reason="Organize your desk with proper lighting"),
            ProductRelationship(product_id="prod_010", related_product_id="prod_020", relationship_type="cross-sell", reason="Better lighting for video calls"),
            ProductRelationship(product_id="prod_021", related_product_id="prod_022", relationship_type="cross-sell", reason="Mount your speaker for better sound"),
            ProductRelationship(product_id="prod_023", related_product_id="prod_024", relationship_type="complementary", reason="Additional portable storage"),
            ProductRelationship(product_id="prod_009", related_product_id="prod_025", relationship_type="complementary", reason="Connect external displays"),
            ProductRelationship(product_id="prod_027", related_product_id="prod_028", relationship_type="cross-sell", reason="Replace or upgrade ear tips"),
            ProductRelationship(product_id="prod_029", related_product_id="prod_007", relationship_type="complementary", reason="Complete laptop cooling setup"),
            ProductRelationship(product_id="prod_016", related_product_id="prod_020", relationship_type="complementary", reason="Lighting for video calls and desk work"),
            ProductRelationship(product_id="prod_030", related_product_id="prod_019", relationship_type="cross-sell", reason="Complete desk organization"),
            ProductRelationship(product_id="prod_018", related_product_id="prod_007", relationship_type="cross-sell", reason="Alternative ergonomic viewing option"),
        ]
        
        for r in relationships:
            db.add(r)
        
        await db.commit()
        print("Seed data created successfully!")

if __name__ == "__main__":
    asyncio.run(seed())
