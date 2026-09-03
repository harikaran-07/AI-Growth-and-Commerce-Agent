"""
Migration: Remove grocery/groceries products from the database.
Run once on production to clean up existing seed data.
"""
import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

GROCERY_CATEGORIES = [
    "Groceries", "Grocery", "Food", "Food & Beverages",
    "Supermarket", "Kitchen & Dining", "Home & Kitchen",
]

GROCERY_KEYWORDS = [
    "rice", "dal", "oil", "tea", "coffee", "snack", "biscuit",
    "chocolate", "noodle", "spice", "flour", "sugar", "salt",
    "detergent", "cleaning", "soap", "shampoo", "toothpaste",
    "cereal", "milk", "juice", "water bottle", "ghee",
    "atta", "pasta", "sauce", "pickle", "jam", "honey",
]


async def remove_groceries():
    from models.database import async_session
    from models.models import Product, CartItem, OrderItem, ProductRelationship
    from sqlalchemy import select, delete, func, text

    async with async_session() as db:
        # Find grocery products
        result = await db.execute(select(Product))
        all_products = result.scalars().all()

        grocery_products = []
        for p in all_products:
            is_grocery = False
            # Check category
            if p.category and any(c.lower() in p.category.lower() for c in GROCERY_CATEGORIES):
                is_grocery = True
            # Check subcategory
            if p.subcategory and any(c.lower() in p.subcategory.lower() for c in GROCERY_CATEGORIES):
                is_grocery = True
            # Check product name/description for grocery keywords
            name_lower = (p.name or "").lower()
            desc_lower = (p.description or "").lower()
            if any(kw in name_lower for kw in GROCERY_KEYWORDS):
                is_grocery = True
            if any(kw in desc_lower for kw in GROCERY_KEYWORDS):
                is_grocery = True
            # Check category for specific grocery subcategories
            if p.category == "Kitchen & Dining" and p.subcategory in ("Cookware", "Appliances"):
                is_grocery = False  # Keep kitchen electronics/appliances
            if is_grocery:
                grocery_products.append(p)

        if not grocery_products:
            logger.info("No grocery products found. Database is clean.")
            return

        grocery_ids = [p.id for p in grocery_products]
        logger.info(f"Found {len(grocery_products)} grocery products to remove")

        # Log what we're removing
        for p in grocery_products[:10]:
            logger.info(f"  - {p.name} (category={p.category}, subcategory={p.subcategory})")
        if len(grocery_products) > 10:
            logger.info(f"  ... and {len(grocery_products) - 10} more")

        # Remove product relationships involving grocery products
        for pid in grocery_ids:
            await db.execute(
                delete(ProductRelationship).where(
                    (ProductRelationship.product_id == pid) |
                    (ProductRelationship.related_product_id == pid)
                )
            )

        # Delete grocery products (CartItem/OrderItem foreign keys may reference them,
        # but we only delete products that have NO order history)
        safe_to_delete = []
        skipped = 0
        for p in grocery_products:
            # Check if product has been ordered
            order_count = await db.execute(
                select(func.count(OrderItem.id)).where(OrderItem.product_id == p.id)
            )
            has_orders = (order_count.scalar() or 0) > 0
            if has_orders:
                skipped += 1
                logger.info(f"  Skipping {p.name} (has order history)")
            else:
                safe_to_delete.append(p)

        if safe_to_delete:
            for p in safe_to_delete:
                # Remove cart items first
                await db.execute(
                    delete(CartItem).where(CartItem.product_id == p.id)
                )
                await db.delete(p)

        await db.commit()
        logger.info(f"Migration complete: removed {len(safe_to_delete)} grocery products, skipped {skipped} (has orders)")


if __name__ == "__main__":
    asyncio.run(remove_groceries())
