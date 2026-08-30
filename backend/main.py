"""
MerchantFlow AI - Main Application
AI Growth & Agentic Commerce Agent for Razorpay Buildathon

Unified deployment: serves both the API and the frontend.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
from models.database import engine, Base, init_db
from routes import products, carts, payments, agent, audit, analytics, policies, approvals, webhooks
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Path to the Next.js static export output
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "frontend", "out")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - initialize database on startup."""
    logger.info("Initializing database...")
    await init_db()
    logger.info("Running seed data...")
    try:
        from seed import seed
        await seed()
    except Exception as e:
        logger.error(f"Seed failed: {e}")
    logger.info("MerchantFlow AI started successfully")
    yield
    logger.info("MerchantFlow AI shutting down")


app = FastAPI(
    title="MerchantFlow AI",
    description="AI Growth & Agentic Commerce Agent for Razorpay Buildathon",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration - support both localhost and production
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "").split(",") if os.getenv("ALLOWED_ORIGINS") else []

default_origins = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3000",
]

for origin in ALLOWED_ORIGINS:
    origin = origin.strip()
    if origin and origin not in default_origins:
        default_origins.append(origin)

# Also add the frontend URL if set
frontend_url = os.getenv("NEXT_PUBLIC_API_URL", "")
if frontend_url:
    from urllib.parse import urlparse
    parsed = urlparse(frontend_url)
    origin = f"{parsed.scheme}://{parsed.netloc}"
    if origin not in default_origins:
        default_origins.append(origin)

app.add_middleware(
    CORSMiddleware,
    allow_origins=default_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers FIRST (before static files)
app.include_router(products.router, prefix="/api/products", tags=["Products"])
app.include_router(carts.router, prefix="/api/carts", tags=["Carts"])
app.include_router(payments.router, prefix="/api/payments", tags=["Payments"])
app.include_router(agent.router, prefix="/api/agent", tags=["Agent"])
app.include_router(audit.router, prefix="/api/audit", tags=["Audit"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])
app.include_router(policies.router, prefix="/api/policies", tags=["Policies"])
app.include_router(approvals.router, prefix="/api/approvals", tags=["Approvals"])
app.include_router(webhooks.router, prefix="/api/webhooks", tags=["Webhooks"])


@app.get("/debug/ai")
async def debug_ai():
    import os
    key = os.getenv("GEMINI_API_KEY", os.getenv("AI_API_KEY", ""))
    model = os.getenv("GEMINI_MODEL", os.getenv("AI_MODEL", "not set"))
    provider = os.getenv("AI_PROVIDER", "not set")
    key_len = len(key) if key else 0
    key_valid = key_len > 10 and key not in ("your_api_key_here", "")
    return {"provider": provider, "model": model, "key_len": key_len, "key_valid": key_valid, "has_key": bool(key)}

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "merchantflow"}


# Serve Next.js static frontend
if os.path.isdir(os.path.join(FRONTEND_DIR, "_next")):
    # Mount _next/static for JS/CSS chunks
    app.mount("/_next", StaticFiles(directory=os.path.join(FRONTEND_DIR, "_next")), name="_next_static")

    # Known Next.js static export page paths
    KNOWN_PAGES = [
        "", "buyer", "products", "cart", "payments",
        "audit", "analytics", "settings"
    ]

    @app.get("/{full_path:path}")
    async def serve_frontend(request: Request, full_path: str):
        """Catch-all route to serve Next.js static pages."""
        # Try exact file first (e.g., /favicon.ico, /image.png)
        file_path = os.path.join(FRONTEND_DIR, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)

        # Try directory with index.html (Next.js static export pattern)
        index_path = os.path.join(FRONTEND_DIR, full_path, "index.html")
        if os.path.isfile(index_path):
            return FileResponse(index_path)

        # Try adding .html extension
        html_path = os.path.join(FRONTEND_DIR, f"{full_path}.html")
        if os.path.isfile(html_path):
            return FileResponse(html_path)

        # Fallback to 404 page or root
        not_found = os.path.join(FRONTEND_DIR, "404.html")
        if os.path.isfile(not_found):
            return FileResponse(not_found, status_code=404)

        # Last resort: serve root index
        root_index = os.path.join(FRONTEND_DIR, "index.html")
        if os.path.isfile(root_index):
            return FileResponse(root_index, status_code=404)

        return {"message": "MerchantFlow AI - Buildathon API", "version": "1.0.0"}

else:
    # Frontend not built yet - just serve API root
    @app.get("/")
    async def root():
        return {"message": "MerchantFlow AI - Buildathon API", "version": "1.0.0"}
