"""
BharatSHIELD FastAPI Application Entrypoint.
"""

import time
from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.database.connection import init_db, SessionLocal, get_db
from backend.app.services.risk_engine import risk_engine
from backend.app.api import (
    transactions, risk, analytics, alerts, assistant, auth,
    fraud_network, threats, simulator, cases, merchant_posture,
    audit, webhooks
)
from backend.app.models.transaction import Transaction
from backend.app.providers.registry import ProviderRegistry

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("bharatshield")

# Metrics state
_request_count = 0
_error_count = 0
_total_latency_ms = 0.0

def _seed_if_empty():
    """Idempotent: seeds demo data only when the transactions table is empty."""
    try:
        db = SessionLocal()
        count = db.query(Transaction).count()
        db.close()
        if count > 0:
            logger.info(f"Database already contains {count} transactions — skipping seed.")
            return
        logger.info("Database is empty — running demo seed pipeline...")
        from scripts.seed_database import seed
        seed()
        logger.info("Demo seed pipeline completed.")
    except Exception as exc:
        logger.error(f"Auto-seed failed (non-fatal): {exc}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing BharatSHIELD database schema...")
    init_db()
    logger.info("Loading ML fraud model and SHAP explainability engine...")
    risk_engine.load_artifacts()
    _seed_if_empty()
    logger.info("BharatSHIELD ready to process live transactions.")
    yield
    logger.info("BharatSHIELD shutting down gracefully.")

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=(
        "Explainable, ML-powered fraud & risk intelligence platform for payment merchants. "
        "Every risk score comes with why it was flagged (SHAP) and what to do about it (automated policies), "
        "backed by an immutable audit trail."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Metrics Middleware
@app.middleware("http")
async def track_metrics_middleware(request: Request, call_next):
    global _request_count, _error_count, _total_latency_ms
    start_time = time.time()
    try:
        response = await call_next(request)
        if response.status_code >= 400:
            _error_count += 1
        return response
    except Exception:
        _error_count += 1
        raise
    finally:
        latency_ms = (time.time() - start_time) * 1000.0
        _request_count += 1
        _total_latency_ms += latency_ms

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Routers
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(transactions.router, prefix=settings.API_V1_STR)
app.include_router(risk.router, prefix=settings.API_V1_STR)
app.include_router(analytics.router, prefix=settings.API_V1_STR)
app.include_router(alerts.router, prefix=settings.API_V1_STR)
app.include_router(assistant.router, prefix=settings.API_V1_STR)
app.include_router(fraud_network.router, prefix=settings.API_V1_STR)
app.include_router(threats.router, prefix=settings.API_V1_STR)
app.include_router(simulator.router, prefix=settings.API_V1_STR)
app.include_router(cases.router, prefix=settings.API_V1_STR)
app.include_router(merchant_posture.router, prefix=settings.API_V1_STR)
app.include_router(audit.router, prefix=settings.API_V1_STR)
app.include_router(webhooks.router, prefix=settings.API_V1_STR)

@app.get("/", tags=["System"])
def root():
    return {
        "name": "BharatSHIELD — AI-Powered Merchant Risk Intelligence Platform",
        "version": "1.0.0",
        "status": "OPERATIONAL",
        "docs": "/docs",
        "model_loaded": risk_engine.model is not None,
        "explainer_loaded": risk_engine.explainer is not None
    }

@app.get("/health", tags=["System"])
def health_check():
    return {
        "status": "healthy",
        "db": "connected",
        "ml_engine": "online" if risk_engine.model is not None else "degraded"
    }

@app.get("/metrics", tags=["System"])
def get_metrics(db: Session = Depends(get_db)):
    avg_latency = round(_total_latency_ms / max(_request_count, 1), 2)
    error_rate = round(_error_count / max(_request_count, 1), 4)
    provider_stats = {}
    try:
        from sqlalchemy import func
        rows = db.query(Transaction.provider, func.count(Transaction.id)).group_by(Transaction.provider).all()
        provider_stats = {provider: count for provider, count in rows}
    except Exception:
        pass

    return {
        "status": "healthy",
        "total_requests": _request_count,
        "error_count": _error_count,
        "error_rate": error_rate,
        "avg_latency_ms": avg_latency,
        "model_inference_loaded": risk_engine.model is not None,
        "explainer_loaded": risk_engine.explainer is not None,
        "registered_providers": ProviderRegistry.list_providers(),
        "provider_stats": provider_stats
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
