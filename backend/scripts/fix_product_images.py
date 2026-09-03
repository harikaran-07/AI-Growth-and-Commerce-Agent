"""
Migration: Fix product image URLs to be product-specific.
Updates all products that still use the old generic brand+subcategory placeholder.
Uses product ID hash to guarantee uniqueness even for variant products.
"""
import asyncio
import logging
import re
import hashlib

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _product_color(product_id: str) -> str:
    """Generate a consistent dark color from product ID for visual variety."""
    h = hashlib.md5(product_id.encode()).hexdigest()[:6]
    # Keep it dark (low RGB values) so white text is readable
    r = min(int(h[0:2], 16) // 3, 40)
    g = min(int(h[2:4], 16) // 3, 40)
    b = min(int(h[4:6], 16) // 3, 60)
    return f"{r:02x}{g:02x}{b:02x}"


async def fix_images():
    from models.database import async_session
    from models.models import Product
    from sqlalchemy import select

    async with async_session() as db:
        result = await db.execute(select(Product))
        products = result.scalars().all()

        updated = 0
        skipped = 0
        for p in products:
            needs_update = False

            if not p.image_url:
                needs_update = True
            elif 'placehold.co' in p.image_url:
                text_match = re.search(r'text=([^&]+)', p.image_url)
                if text_match:
                    current_text = text_match.group(1)
                    parts = current_text.split('+')
                    # Old format had <=2 parts (Brand+Subcategory)
                    if len(parts) <= 2:
                        needs_update = True

            if needs_update and p.name:
                # Use product name + first 8 chars of ID for guaranteed uniqueness
                name_text = p.name[:16].replace(' ', '+')
                id_suffix = p.id[:8]
                color = _product_color(p.id)
                p.image_url = f"https://placehold.co/400x300/{color}/ffffff?text={name_text}+{id_suffix}"
                updated += 1
            else:
                skipped += 1

        await db.commit()
        logger.info(f"Image migration complete: {updated} updated, {skipped} skipped")


if __name__ == "__main__":
    asyncio.run(fix_images())
