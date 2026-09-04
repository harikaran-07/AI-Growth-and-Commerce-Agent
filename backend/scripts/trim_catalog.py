"""
Migration: Keep the catalog within the project's 5,000-product maximum.

Only acts when the products table exceeds 5,000 rows (legacy over-seeded DBs).
Preserves every product referenced by an order (OrderItem), then keeps the
highest-revenue products for the remaining slots. Removes only synthetic
catalog rows — never orders, payments, or audit history.
"""

import logging

logger = logging.getLogger(__name__)

MAX_PRODUCTS = 5000


async def trim_catalog():
    from models.database import async_session
    from models.models import Product, ProductRelationship, OrderItem, CartItem
    from sqlalchemy import select, func

    async with async_session() as db:
        total = (await db.execute(select(func.count(Product.id)))).scalar() or 0
        if total <= MAX_PRODUCTS:
            logger.info(f"Catalog has {total} products (within {MAX_PRODUCTS} limit) - no trim needed")
            return

        # Products referenced by historical orders must never be deleted
        order_refs = await db.execute(
            select(OrderItem.product_id).distinct()
        )
        protected_ids = {row[0] for row in order_refs.all()}

        # Keep protected products first, then fill remaining slots with
        # the highest-revenue products so best sellers / flagship items survive
        all_ids = (await db.execute(select(Product.id))).scalars().all()
        remaining_slots = MAX_PRODUCTS - len(protected_ids)
        if remaining_slots < 0:
            logger.error("More order-referenced products than catalog limit; skipping trim")
            return

        keep = set(protected_ids)
        if remaining_slots > 0:
            revenue_rows = await db.execute(
                select(Product.id)
                .where(Product.id.notin_(protected_ids))
                .order_by(Product.revenue.desc(), Product.sales.desc())
                .limit(remaining_slots)
            )
            keep.update(revenue_rows.scalars().all())

        to_delete = [pid for pid in all_ids if pid not in keep]
        logger.info(f"Trimming catalog: {total} -> keep {len(keep)} (deleting {len(to_delete)} synthetic products)")

        # Remove relationship and cart rows referencing deleted products first
        if to_delete:
            rels = await db.execute(
                select(ProductRelationship).where(
                    ProductRelationship.product_id.in_(to_delete)
                )
            )
            for r in rels.scalars().all():
                await db.delete(r)

            cart_items = await db.execute(
                select(CartItem).where(CartItem.product_id.in_(to_delete))
            )
            for ci in cart_items.scalars().all():
                await db.delete(ci)

            await db.commit()

            products = await db.execute(
                select(Product).where(Product.id.in_(to_delete))
            )
            for p in products.scalars().all():
                await db.delete(p)
            await db.commit()

        final = (await db.execute(select(func.count(Product.id)))).scalar() or 0
        logger.info(f"Catalog trim complete: {final} products")
