"""
AI Growth and Commerce Agent - Main Application
AI Growth & Agentic Commerce Agent for Razorpay Buildathon

Unified deployment: serves both the API and the frontend.
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from contextlib import asynccontextmanager
from models.database import engine, Base, init_db
from routes import products, carts, payments, agent, audit, analytics, policies, approvals, webhooks
from routes import orders, notifications, pricing, synthetic, campaigns
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

FRONTEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "frontend", "out")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - initialize database on startup."""
    logger.info("Initializing database schema...")
    await init_db()
    
    # Seed products ONLY if the database is empty (first deploy / fresh DB)
    # NEVER reseed on restart - this preserves real orders and inventory
    try:
        from models.database import async_session
        from sqlalchemy import text
        async with async_session() as db:
            result = await db.execute(text("SELECT COUNT(*) FROM products"))
            count = result.scalar()
            
            if count == 0:
                # First time - seed the catalog
                logger.info("Empty database detected. Seeding product catalog...")
                from seed import seed
                await seed()
                logger.info("Seed completed successfully")
            else:
                # Database already has products - NEVER reseed
                logger.info(f"Found {count} products in database - skipping seed (preserving existing data)")

            # One-time migration: remove grocery products
            grocery_check = await db.execute(
                text("SELECT COUNT(*) FROM products WHERE category LIKE '%Grocer%' OR category LIKE '%grocer%'")
            )
            grocery_count = grocery_check.scalar() or 0
            if grocery_count > 0:
                logger.info(f"Found {grocery_count} grocery products - removing")
                try:
                    from scripts.remove_groceries import remove_groceries
                    await remove_groceries()
                except Exception as ge:
                    logger.error(f"Grocery cleanup failed: {ge}")

            # Fix product images: ensure each product has a unique, product-specific image
            try:
                from scripts.fix_product_images import fix_images
                await fix_images()
            except Exception as ie:
                logger.error(f"Image fix migration failed: {ie}")

            # Keep catalog within spec maximum (5,000 products) on legacy over-seeded DBs
            try:
                from scripts.trim_catalog import trim_catalog
                await trim_catalog()
            except Exception as te:
                logger.error(f"Catalog trim migration failed: {te}")

            # One-time migration: add campaign policy columns on legacy DBs
            try:
                from scripts.migrate_policy_columns import migrate_policy_columns
                await migrate_policy_columns()
            except Exception as mpc:
                logger.error(f"Policy column migration failed: {mpc}")

    except Exception as e:
        logger.error(f"Startup check failed: {e}")
        import traceback
        traceback.print_exc()
    
    logger.info("AI Growth and Commerce Agent started successfully")
    yield
    logger.info("AI Growth and Commerce Agent shutting down")


app = FastAPI(
    title="AI Growth and Commerce Agent",
    description="Commerce Agent for Razorpay Buildathon",
    version="2.1.0",
    lifespan=lifespan
)

# CORS - restrict to production origins
allowed_origins = os.getenv("ALLOWED_ORIGINS", "").split(",") if os.getenv("ALLOWED_ORIGINS") else [
    "https://ai-growth-and-commerce-agent.onrender.com",
    "http://localhost:3000",
    "http://localhost:8000",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global error handler - returns consistent JSON error responses."""
    logger.error(f"Unhandled exception: {type(exc).__name__}: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred. Please try again."
            }
        }
    )

# Include API routers
app.include_router(products.router, prefix="/api/products", tags=["Products"])
app.include_router(carts.router, prefix="/api/carts", tags=["Carts"])
app.include_router(payments.router, prefix="/api/payments", tags=["Payments"])
app.include_router(agent.router, prefix="/api/agent", tags=["Agent"])
app.include_router(audit.router, prefix="/api/audit", tags=["Audit"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])
app.include_router(policies.router, prefix="/api/policies", tags=["Policies"])
app.include_router(approvals.router, prefix="/api/approvals", tags=["Approvals"])
app.include_router(webhooks.router, prefix="/api/webhooks", tags=["Webhooks"])
app.include_router(orders.router, prefix="/api/orders", tags=["Orders"])
app.include_router(notifications.router, prefix="/api/notifications", tags=["Notifications"])
app.include_router(pricing.router, prefix="/api/pricing", tags=["Pricing"])
app.include_router(synthetic.router, prefix="/api", tags=["Synthetic Data"])
app.include_router(campaigns.router, prefix="/api/campaigns", tags=["Campaigns"])


@app.get("/health")
async def health():
    """Health check endpoint - returns 200 when healthy."""
    razorpay_key = os.getenv("RAZORPAY_KEY_ID", "")
    
    # Check database connectivity
    db_status = "unknown"
    db_type = "unknown"
    try:
        from models.database import async_session, IS_POSTGRES
        from sqlalchemy import text
        async with async_session() as db:
            await db.execute(text("SELECT 1"))
            db_status = "connected"
            db_type = "postgresql" if IS_POSTGRES else "sqlite"
    except Exception as e:
        db_status = f"error: {type(e).__name__}"
        db_type = "unknown"
    
    return {
        "status": "healthy",
        "service": "AI Growth and Commerce Agent",
        "version": "2.1.0",
        "chatbot": {
            "type": "rule-based",
            "provider": "built-in",
            "mode": "local",
        },
        "razorpay": "test_mode" if razorpay_key.startswith("rzp_test_") else ("configured" if razorpay_key else "demo_mode"),
        "database": {
            "status": db_status,
            "type": db_type,
        },
    }


# ── Frontend static file serving ────────────────────────────────
# We use a middleware so that it ONLY runs when no FastAPI route
# matched (i.e. it won't intercept /api/* or /health requests).
# ────────────────────────────────────────────────────────────────

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        return response


class FrontendStaticMiddleware(BaseHTTPMiddleware):
    """Serve Next.js static export files for non-API routes.
    
    This middleware only activates when the FastAPI router returns 404,
    meaning no API route or health route matched. It then tries to serve
    static files from the frontend/out directory.
    """
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Only intercept 404 responses for non-API paths
        if response.status_code != 404:
            return response
        
        path = request.url.path
        
        # Skip API, docs, and internal paths
        if (path.startswith("/api/") or path == "/api" or
                path.startswith("/health") or
                path.startswith("/docs") or path.startswith("/openapi") or
                path.startswith("/redoc") or path.startswith("/_next") or
                path.startswith("/favicon")):
            return response
        
        # Try to serve from frontend/out directory
        return await self._serve_frontend(path)
    
    async def _serve_frontend(self, path: str):
        """Try to serve a static file from the frontend output directory."""
        if not os.path.isdir(FRONTEND_DIR):
            return JSONResponse(status_code=404, content={"error": "Frontend not built"})
        
        # Strip leading slash
        rel = path.lstrip("/")
        
        # 1. Exact file match
        file_path = os.path.join(FRONTEND_DIR, rel)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        
        # 2. Directory index.html
        index_path = os.path.join(FRONTEND_DIR, rel, "index.html")
        if os.path.isfile(index_path):
            return FileResponse(index_path)
        
        # 3. .html extension (Next.js static export: /products -> products.html)
        html_path = os.path.join(FRONTEND_DIR, f"{rel}.html")
        if os.path.isfile(html_path):
            return FileResponse(html_path)
        
        # 4. Fallback to 404.html
        not_found = os.path.join(FRONTEND_DIR, "404.html")
        if os.path.isfile(not_found):
            return FileResponse(not_found, status_code=404)
        
        # 5. Last resort: root index.html
        root_index = os.path.join(FRONTEND_DIR, "index.html")
        if os.path.isfile(root_index):
            return FileResponse(root_index, status_code=404)
        
        return JSONResponse(status_code=404, content={"error": "Not found"})


# Mount static assets (CSS/JS bundles) and add the frontend middleware
if os.path.isdir(os.path.join(FRONTEND_DIR, "_next")):
    app.mount("/_next", StaticFiles(directory=os.path.join(FRONTEND_DIR, "_next")), name="_next_static")

# Add security headers middleware
app.add_middleware(SecurityHeadersMiddleware)

# Add frontend middleware LAST (runs after all route matching)
app.add_middleware(FrontendStaticMiddleware)
