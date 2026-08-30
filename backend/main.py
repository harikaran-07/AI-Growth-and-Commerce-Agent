"""
MerchantFlow AI - Main Application
AI Growth & Agentic Commerce Agent for Razorpay Buildathon
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from models.database import engine, Base, init_db
from routes import products, carts, payments, agent, audit, analytics, policies, approvals, webhooks
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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

# Always allow localhost for development
default_origins = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3000",
]

# Add production origins from environment
for origin in ALLOWED_ORIGINS:
    origin = origin.strip()
    if origin and origin not in default_origins:
        default_origins.append(origin)

# Also add the frontend URL if set
frontend_url = os.getenv("NEXT_PUBLIC_API_URL", "")
if frontend_url:
    # Extract origin from full URL
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

# Include routers
app.include_router(products.router, prefix="/api/products", tags=["Products"])
app.include_router(carts.router, prefix="/api/carts", tags=["Carts"])
app.include_router(payments.router, prefix="/api/payments", tags=["Payments"])
app.include_router(agent.router, prefix="/api/agent", tags=["Agent"])
app.include_router(audit.router, prefix="/api/audit", tags=["Audit"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])
app.include_router(policies.router, prefix="/api/policies", tags=["Policies"])
app.include_router(approvals.router, prefix="/api/approvals", tags=["Approvals"])
app.include_router(webhooks.router, prefix="/api/webhooks", tags=["Webhooks"])


@app.get("/")
async def root():
    return {"message": "MerchantFlow AI - Buildathon API", "version": "1.0.0"}


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "merchantflow-backend"}
