"""
BharatSHIELD FastAPI Application Entrypoint.
"""

from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.core.config import settings
from backend.app.database.connection import init_db
from backend.app.services.risk_engine import risk_engine
from backend.app.api import transactions, risk, analytics, alerts, assistant, auth, fraud_network, threats, simulator, cases, merchant_posture, audit

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("bharatshield")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing BharatSHIELD database schema...")
    init_db()
    logger.info("Loading ML fraud model and SHAP explainability engine...")
    risk_engine.load_artifacts()
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
