from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from models.database import get_db
from models.models import Product, ProductRelationship
from pydantic import BaseModel
from typing import Optional, List

router = APIRouter()

class ProductResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    category: str
    price: float
    currency: str
    stock: int
    image_url: Optional[str]

class CatalogProduct(BaseModel):
    product_id: str
    name: str
    description: Optional[str]
    category: str
    price: float
    currency: str
    stock: int
    availability: bool
    related_products: List[str]
    complementary_products: List[str]

@router.get("/", response_model=List[ProductResponse])
async def get_products(
    category: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    in_stock: bool = True,
    db: AsyncSession = Depends(get_db)
):
    query = select(Product)
    conditions = []
    if category:
        conditions.append(Product.category == category)
    if min_price is not None:
        conditions.append(Product.price >= min_price)
    if max_price is not None:
        conditions.append(Product.price <= max_price)
    if in_stock:
        conditions.append(Product.stock > 0)
    if conditions:
        query = query.where(and_(*conditions))
    result = await db.execute(query)
    products = result.scalars().all()
    return products

@router.get("/agent/catalog", response_model=List[CatalogProduct])
async def get_agent_catalog(db: AsyncSession = Depends(get_db)):
    products_result = await db.execute(select(Product))
    products = products_result.scalars().all()
    catalog = []
    for p in products:
        rels_result = await db.execute(
            select(ProductRelationship).where(ProductRelationship.product_id == p.id)
        )
        rels = rels_result.scalars().all()
        related = [r.related_product_id for r in rels if r.relationship_type in ("cross-sell", "complementary")]
        complementary = [r.related_product_id for r in rels if r.relationship_type == "upsell"]
        catalog.append(CatalogProduct(
            product_id=p.id,
            name=p.name,
            description=p.description,
            category=p.category,
            price=p.price,
            currency=p.currency,
            stock=p.stock,
            availability=p.stock > 0,
            related_products=related,
            complementary_products=complementary
        ))
    return catalog

@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(product_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product
