from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
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
    subcategory: Optional[str]
    brand: Optional[str]
    price: float
    currency: str
    stock: int
    sku: Optional[str]
    rating: Optional[float]
    tags: Optional[str]
    image_url: Optional[str]

    class Config:
        from_attributes = True


class ProductListResponse(BaseModel):
    products: List[ProductResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


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


@router.get("/", response_model=ProductListResponse)
async def get_products(
    category: Optional[str] = None,
    subcategory: Optional[str] = None,
    brand: Optional[str] = None,
    q: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    in_stock: bool = True,
    sort_by: Optional[str] = "name",
    sort_order: Optional[str] = "asc",
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """Get products with filtering, search, and pagination."""
    query = select(Product)
    count_query = select(func.count(Product.id))
    conditions = []

    if category:
        conditions.append(Product.category == category)
    if subcategory:
        conditions.append(Product.subcategory == subcategory)
    if brand:
        conditions.append(Product.brand == brand)
    if min_price is not None:
        conditions.append(Product.price >= min_price)
    if max_price is not None:
        conditions.append(Product.price <= max_price)
    if in_stock:
        conditions.append(Product.stock > 0)

    # Text search across name, description, tags, brand
    if q:
        search_term = f"%{q}%"
        conditions.append(
            or_(
                Product.name.ilike(search_term),
                Product.description.ilike(search_term),
                Product.tags.ilike(search_term),
                Product.brand.ilike(search_term),
                Product.category.ilike(search_term),
                Product.subcategory.ilike(search_term),
            )
        )

    if conditions:
        query = query.where(and_(*conditions))
        count_query = count_query.where(and_(*conditions))

    # Count total
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Sort
    sort_col = getattr(Product, sort_by, Product.name)
    if sort_order == "desc":
        query = query.order_by(sort_col.desc())
    else:
        query = query.order_by(sort_col.asc())

    # Paginate
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    result = await db.execute(query)
    products = result.scalars().all()

    return ProductListResponse(
        products=products,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.get("/agent/catalog", response_model=List[CatalogProduct])
async def get_agent_catalog(db: AsyncSession = Depends(get_db)):
    """Get agent-readable catalog (limited to avoid overwhelming LLM)."""
    products_result = await db.execute(
        select(Product).where(Product.stock > 0).limit(500)
    )
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


@router.get("/search")
async def search_products(
    q: str = Query(..., min_length=1),
    category: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db)
):
    """Full-text product search."""
    query = select(Product)
    count_query = select(func.count(Product.id))
    conditions = [Product.stock > 0]

    search_term = f"%{q}%"
    conditions.append(
        or_(
            Product.name.ilike(search_term),
            Product.description.ilike(search_term),
            Product.tags.ilike(search_term),
            Product.brand.ilike(search_term),
            Product.subcategory.ilike(search_term),
        )
    )

    if category:
        conditions.append(Product.category == category)
    if min_price is not None:
        conditions.append(Product.price >= min_price)
    if max_price is not None:
        conditions.append(Product.price <= max_price)

    where_clause = and_(*conditions)
    query = query.where(where_clause)
    count_query = count_query.where(where_clause)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    offset = (page - 1) * page_size
    query = query.order_by(Product.rating.desc().nullslast(), Product.name).offset(offset).limit(page_size)

    result = await db.execute(query)
    products = result.scalars().all()

    return {
        "products": [
            {
                "id": p.id,
                "name": p.name,
                "description": p.description,
                "category": p.category,
                "subcategory": p.subcategory,
                "brand": p.brand,
                "price": p.price,
                "currency": p.currency,
                "stock": p.stock,
                "rating": p.rating,
            }
            for p in products
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/categories")
async def get_categories(db: AsyncSession = Depends(get_db)):
    """Get all categories with product counts."""
    result = await db.execute(
        select(Product.category, func.count(Product.id))
        .where(Product.stock > 0)
        .group_by(Product.category)
        .order_by(func.count(Product.id).desc())
    )
    categories = [{"name": row[0], "count": row[1]} for row in result.all()]
    return categories


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(product_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product
