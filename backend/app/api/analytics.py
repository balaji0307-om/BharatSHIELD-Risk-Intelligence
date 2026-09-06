"""
Analytics API endpoints: KPIs, volume & fraud trends, and real model evaluation metrics.
"""

import os
import json
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.app.database.connection import get_db
from backend.app.core.config import settings
from backend.app.core.security import get_current_merchant_id
from backend.app.database.repositories import AnalyticsRepository

router = APIRouter(prefix="/analytics", tags=["Analytics & Model Metrics"])

@router.get("/overview", summary="Merchant KPI Overview")
def get_overview(
    merchant_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_merchant: str = Depends(get_current_merchant_id)
):
    effective_merchant = merchant_id or current_merchant
    kpis = AnalyticsRepository.get_overview_kpis(db, merchant_id=effective_merchant)
    return kpis

@router.get("/trends", summary="24-Hour Risk & Volume Trends")
def get_trends(
    merchant_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_merchant: str = Depends(get_current_merchant_id)
):
    effective_merchant = merchant_id or current_merchant
    trends = AnalyticsRepository.get_trends(db, merchant_id=effective_merchant)
    return {"trends": trends}

@router.get("/model", summary="Trained Model Performance & Architecture Metrics")
def get_model_metrics():
    """
    Returns authentic, non-fabricated metrics directly from the evaluated model artifact:
    Precision, Recall, F1-Score, AUC-ROC, False Positive Rate, and Model Tournament Comparison.
    """
    cfg_path = settings.FEATURE_CONFIG_PATH
    if os.path.exists(cfg_path):
        with open(cfg_path, "r") as f:
            config_data = json.load(f)
        return config_data
        
    return {
        "model_version": "1.0.0",
        "model_name": "xgboost",
        "status": "Model artifact configuration not found. Please run train_model.py."
    }
