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
    previous_price: Optional[float]
    cost_price: Optional[float]
    currency: str
    stock: int
    sales: int
    revenue: float
    margin: float
    sku: Optional[str]
    rating: Optional[float]
    tags: Optional[str]
    image_url: Optional[str]
    is_active: bool

    class Config:
        from_attributes = True


class ProductListResponse(BaseModel):
    products: List[ProductResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    cost_price: Optional[float] = None
    stock: Optional[int] = None
    category: Optional[str] = None
    is_active: Optional[bool] = None


@router.get("/", response_model=ProductListResponse)
async def get_products(
    category: Optional[str] = None,
    subcategory: Optional[str] = None,
    brand: Optional[str] = None,
    q: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    min_stock: Optional[int] = None,
    in_stock: Optional[bool] = None,
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
    if in_stock is True:
        conditions.append(Product.stock > 0)
    elif in_stock is False:
        conditions.append(Product.stock == 0)
    if min_stock is not None:
        conditions.append(Product.stock <= min_stock)

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
                Product.sku.ilike(search_term),
            )
        )

    if conditions:
        query = query.where(and_(*conditions))
        count_query = count_query.where(and_(*conditions))

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    sort_col = getattr(Product, sort_by, Product.name)
    if sort_order == "desc":
        query = query.order_by(sort_col.desc())
    else:
        query = query.order_by(sort_col.asc())

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


@router.get("/categories")
async def get_categories(db: AsyncSession = Depends(get_db)):
    """Get all categories with product counts."""
    result = await db.execute(
        select(Product.category, func.count(Product.id))
        .group_by(Product.category)
        .order_by(func.count(Product.id).desc())
    )
    categories = [{"name": row[0], "count": row[1]} for row in result.all()]
    return categories


@router.get("/brands")
async def get_brands(category: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    """Get all brands with product counts."""
    query = select(Product.brand, func.count(Product.id)).where(Product.brand.isnot(None))
    if category:
        query = query.where(Product.category == category)
    query = query.group_by(Product.brand).order_by(func.count(Product.id).desc())
    result = await db.execute(query)
    brands = [{"name": row[0], "count": row[1]} for row in result.all()]
    return brands


@router.get("/stats")
async def get_product_stats(db: AsyncSession = Depends(get_db)):
    """Get aggregate product statistics."""
    total = await db.execute(select(func.count(Product.id)))
    total_count = total.scalar() or 0

    low_stock = await db.execute(
        select(func.count(Product.id)).where(Product.stock > 0, Product.stock <= 10)
    )
    low_stock_count = low_stock.scalar() or 0

    out_of_stock = await db.execute(
        select(func.count(Product.id)).where(Product.stock == 0)
    )
    out_of_stock_count = out_of_stock.scalar() or 0

    avg_price = await db.execute(select(func.avg(Product.price)))
    avg = avg_price.scalar() or 0

    total_revenue = await db.execute(select(func.sum(Product.revenue)))
    rev = total_revenue.scalar() or 0

    avg_margin = await db.execute(
        select(func.avg(Product.margin)).where(Product.margin > 0)
    )
    avg_m = avg_margin.scalar() or 0

    return {
        "total_products": total_count,
        "in_stock": total_count - out_of_stock_count,
        "low_stock": low_stock_count,
        "out_of_stock": out_of_stock_count,
        "avg_price": round(avg, 2),
        "total_revenue": round(rev, 2),
        "avg_margin": round(avg_m, 2),
    }


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(product_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(product_id: str, update: ProductUpdate, db: AsyncSession = Depends(get_db)):
    """Update a product's details."""
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    if update.name is not None:
        product.name = update.name
    if update.description is not None:
        product.description = update.description
    if update.price is not None:
        if product.cost_price:
            product.margin = round(((update.price - product.cost_price) / update.price) * 100, 2) if update.price > 0 else 0
        product.previous_price = product.price
        product.price = update.price
    if update.cost_price is not None:
        product.cost_price = update.cost_price
        if product.price and product.price > 0:
            product.margin = round(((product.price - update.cost_price) / product.price) * 100, 2)
    if update.stock is not None:
        product.stock = update.stock
    if update.category is not None:
        product.category = update.category
    if update.is_active is not None:
        product.is_active = update.is_active

    await db.commit()
    await db.refresh(product)
    return product


@router.get("/agent/catalog")
async def get_agent_catalog(
    q: Optional[str] = None,
    category: Optional[str] = None,
    in_stock: Optional[bool] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Get paginated agent-readable catalog (full stable fields, searchable).

    Response items use `id` (the stable product UUID also used by the products
    page, product details, chat, cart and orders) so an AI buyer can add the
    exact product to a shared cart. Never index/random-based image mapping.
    """
    query = select(Product)
    count_query = select(func.count(Product.id))
    conditions = []
    if category:
        conditions.append(or_(
            Product.category.ilike(f"%{category}%"),
            Product.subcategory.ilike(f"%{category}%"),
        ))
    if in_stock is True:
        conditions.append(Product.stock > 0)
    elif in_stock is False:
        conditions.append(Product.stock <= 0)
    if q:
        term = f"%{q}%"
        conditions.append(or_(
            Product.name.ilike(term), Product.description.ilike(term),
            Product.brand.ilike(term), Product.category.ilike(term),
            Product.subcategory.ilike(term), Product.sku.ilike(term),
        ))
    if conditions:
        query = query.where(and_(*conditions))
        count_query = count_query.where(and_(*conditions))

    total = (await db.execute(count_query)).scalar() or 0
    query = query.order_by(Product.revenue.desc()).offset((page - 1) * page_size).limit(page_size)
    products = (await db.execute(query)).scalars().all()

    def _agent_item(p):
        discount = 0.0
        if p.previous_price and p.price and p.previous_price > p.price:
            discount = round((p.previous_price - p.price) / p.previous_price * 100, 1)
        return {
            "id": p.id,
            "product_id": p.id,  # alias for backward compatibility
            "sku": p.sku or "",
            "name": p.name,
            "description": p.description or "",
            "brand": p.brand or "",
            "category": p.category,
            "subcategory": p.subcategory or "",
            "price": float(p.price or 0),
            "currency": p.currency or "INR",
            "discount": discount,
            "stock": int(p.stock or 0),
            "availability": bool(p.stock and p.stock > 0 and p.is_active),
            "rating": float(p.rating or 0),
            "image_url": p.image_url or "",
            "product_url": f"/product?id={p.id}",
            "tags": (p.tags or "").split(",") if p.tags else [],
            "sales": int(p.sales or 0),
            "revenue": float(p.revenue or 0),
        }

    return {
        "products": [_agent_item(p) for p in products],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size if total else 0,
    }
