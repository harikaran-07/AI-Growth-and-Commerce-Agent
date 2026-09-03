"""
Migration: Fix product image URLs to be product-specific.
Updates all products that still use the old generic brand+subcategory placeholder.
"""
import asyncio
import logging
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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
            # Check if using old generic placeholder (brand+subcategory pattern)
            if p.image_url and 'placehold.co' in p.image_url:
                # Extract the current text from the URL
                text_match = re.search(r'text=([^&]+)', p.image_url)
                if text_match:
                    current_text = text_match.group(1)
                    # Old format: "Brand+Subcategory" (2 parts max)
                    parts = current_text.split('+')
                    if len(parts) <= 2 and p.name:
                        # Update to use product name (truncated to 20 chars)
                        new_text = p.name[:20].replace(' ', '+')
                        new_url = f"https://placehold.co/400x300/1e1b4b/ffffff?text={new_text}"
                        p.image_url = new_url
                        updated += 1
                    else:
                        skipped += 1
                else:
                    skipped += 1
            elif not p.image_url:
                # No image at all - generate one from product name
                if p.name:
                    new_text = p.name[:20].replace(' ', '+')
                    p.image_url = f"https://placehold.co/400x300/1e1b4b/ffffff?text={new_text}"
                    updated += 1
                else:
                    skipped += 1
            else:
                # Has a custom image URL - keep it
                skipped += 1

        await db.commit()
        logger.info(f"Image migration complete: {updated} updated, {skipped} skipped (already correct or custom)")


if __name__ == "__main__":
    asyncio.run(fix_images())
