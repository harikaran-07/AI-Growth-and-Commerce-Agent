"""
AI Growth and Commerce Agent - Main Application
AI Growth & Agentic Commerce Agent for Razorpay Buildathon

Unified deployment: serves both the API and the frontend.
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from contextlib import asynccontextmanager
from models.database import engine, Base, init_db
from routes import products, carts, payments, agent, audit, analytics, policies, approvals, webhooks
from routes import orders, notifications, pricing, synthetic
import os
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

FRONTEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "frontend", "out")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - initialize database on startup."""
    logger.info("Initializing database...")
    await init_db()
    logger.info("Running seed data...")
    try:
        from models.database import async_session
        from sqlalchemy import text
        async with async_session() as db:
            result = await db.execute(text("SELECT COUNT(*) FROM products"))
            count = result.scalar()
        if count < 100:
            logger.info(f"Only {count} products, seeding catalog...")
            from seed import seed
            await seed()
            logger.info("Seed completed successfully")
        else:
            logger.info(f"Found {count} products, skipping seed")
    except Exception as e:
        logger.error(f"Seed failed: {e}")
        import traceback
        traceback.print_exc()
    logger.info("AI Growth and Commerce Agent started successfully")
    yield
    logger.info("AI Growth and Commerce Agent shutting down")


app = FastAPI(
    title="AI Growth and Commerce Agent",
    description="AI Growth & Agentic Commerce Agent for Razorpay Buildathon",
    version="2.0.0",
    lifespan=lifespan
)

# CORS - allow all origins for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
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


@app.get("/health")
async def health():
    import os
    # Check Gemini key availability
    key1 = os.getenv("GEMINI_API_KEY_1", os.getenv("GEMINI_API_KEY", ""))
    key2 = os.getenv("GEMINI_API_KEY_2", "")
    has_gemini = bool(key1 and key1 not in ("your_api_key_here", "placeholder_secret", ""))
    has_gemini2 = bool(key2 and key2 not in ("your_api_key_here", "placeholder_secret", ""))
    
    razorpay_key = os.getenv("RAZORPAY_KEY_ID", "")
    return {
        "status": "healthy",
        "service": "merchantflow",
        "version": "2.0.0",
        "ai": {
            "provider": os.getenv("AI_PROVIDER", "gemini"),
            "model": os.getenv("AI_MODEL", "gemini-2.0-flash"),
            "key1_configured": has_gemini,
            "key2_configured": has_gemini2,
            "mode": "live" if has_gemini else "fallback",
        },
        "razorpay": "test_mode" if razorpay_key.startswith("rzp_test_") else ("configured" if razorpay_key else "demo_mode"),
        "database": "connected",
    }


# Serve Next.js static frontend
if os.path.isdir(os.path.join(FRONTEND_DIR, "_next")):
    app.mount("/_next", StaticFiles(directory=os.path.join(FRONTEND_DIR, "_next")), name="_next_static")

    @app.get("/{full_path:path}")
    async def serve_frontend(request: Request, full_path: str):
        file_path = os.path.join(FRONTEND_DIR, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        index_path = os.path.join(FRONTEND_DIR, full_path, "index.html")
        if os.path.isfile(index_path):
            return FileResponse(index_path)
        html_path = os.path.join(FRONTEND_DIR, f"{full_path}.html")
        if os.path.isfile(html_path):
            return FileResponse(html_path)
        not_found = os.path.join(FRONTEND_DIR, "404.html")
        if os.path.isfile(not_found):
            return FileResponse(not_found, status_code=404)
        root_index = os.path.join(FRONTEND_DIR, "index.html")
        if os.path.isfile(root_index):
            return FileResponse(root_index, status_code=404)
        return {"message": "AI Growth and Commerce Agent", "version": "2.0.0"}
else:
    @app.get("/")
    async def root():
        return {"message": "AI Growth and Commerce Agent", "version": "2.0.0"}
