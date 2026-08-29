from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from models.database import engine, Base, init_db
from routes import products, carts, payments, agent, audit, analytics, policies, approvals, webhooks

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

app = FastAPI(
    title="MerchantFlow AI",
    description="AI Growth & Agentic Commerce Agent for Razorpay Buildathon",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    return {"message": "MerchantFlow AI - Buildathon API"}

@app.get("/health")
async def health():
    return {"status": "healthy"}
