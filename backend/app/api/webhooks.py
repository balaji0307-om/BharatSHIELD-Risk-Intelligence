"""
Provider-Unbiased Webhook Ingestion Endpoint.
BharatSHIELD ingests payment events from any registered gateway (R!zpay, Stub, Banks),
normalizes them into CommonTransaction, submits them to the model pipeline,
and persists them with provider attribution.
"""

import json
from datetime import datetime, timezone
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from backend.app.database.connection import get_db
from backend.app.core.config import settings
from backend.app.providers.registry import ProviderRegistry
from backend.app.services.risk_engine import risk_engine
from backend.app.models.transaction import Transaction, Merchant
from backend.app.models.risk_case import RiskScore, RiskFactor, AuditLog
from backend.app.models.alert import Alert
from backend.app.services.audit_chain_service import AuditChainService
from backend.app.database.repositories import TransactionRepository

router = APIRouter(prefix="/webhooks", tags=["Payment Webhooks"])

# Webhook-specific in-memory rate limiter (allows higher burst throughput than auth)
_webhook_hits_by_ip = {}

def _check_webhook_rate_limit(client_ip: Optional[str]) -> None:
    now = datetime.now(timezone.utc).timestamp()
    ip=client_ip or "global_webhook"
    hits = [_t for _t in _webhook_hits_by_ip.get(ip, []) if now - _t <= 60]
    if len(hits) >= settings.WEBHOOK_BURST_RATE_LIMIT:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Webhook burst rate limit exceeded. Please back off."
        )
    hits.append(now)
    _webhook_hits_by_ip[ip] = hits


@router.post("/{provider_name}", summary="Ingest Provider Webhook Event")
async def handle_provider_webhook(
    provider_name: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Receives webhook event from any registered PSP (R!zpay, Stub, etc.),
    verifies signature, normalizes data, evaluates risk, and stores audit.
    """
    client_ip = request.client.host if request.client else None
    _check_webhook_rate_limit(client_ip)

    # 1. Lookup adapter
    adapter = ProviderRegistry.get(provider_name)
    if not adapter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unsupported payment provider: '{provider_name}'. Registered: {ProviderRegistry.list_providers()}"
        )

    # 2. Read raw request body
    raw_body = await request.body()
    if not raw_body:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Webhook payload empty")

    # 3. Signature verification with secret rotation support
    signature = (
        request.headers.get("X-Razorpay-Signature")
        or request.headers.get("X-Webhook-Signature")
        or request.headers.get("X-Signature")
        or ""
    )

    candidate_secrets = []
    if settings.RAZORPAY_WEBHOOK_SECRET:
        candidate_secrets.append(settings.RAZORPAY_WEBHOOK_SECRET)
    if settings.RAZORPAY_WEBHOOK_SECRET_PREVIOUS:
        candidate_secrets.append(settings.RAZORPAY_WEBHOOK_SECRET_PREVIOUS)

    if signature and not adapter.verify_signature(raw_body, signature, candidate_secrets):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid webhook signature for provider '{provider_name}'"
        )

    # 4. Parse and normalize to CommonTransaction
    try:
        event_data = adapter.parse_webhook(raw_body, request.headers)
        common = adapter.normalize(event_data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Parsing or normalization failed: {str(e)}"
        )

    # 5. Ensure merchant exists
    merchant = db.query(Merchant).filter(Merchant.merchant_id == common.merchant_id).first()
    if not merchant:
        merchant = Merchant(
            merchant_id=common.merchant_id,
            name=f"Merchant {common.merchant_id}",
            api_key=f"key_live{common.merchant_id}_secret"
        )
        db.add(merchant)
        db.commit()

    # 6. ML Risk Scoring & Explainability via Provider-Agnostic Engine
    txn_dict = common.to_feature_dict()
    defaults = {
        "device_age_days": 60,
        "failed_attempts": 0,
        "is_new_device": False,
        "is_new_location": False,
        "transactions_last_5min": 0,
        "transactions_last_10min": 0,
        "transactions_last_1hr": 1,
        "amount_last_1hr": common.amount,
        "avg_transaction_amount": common.amount,
        "amount_deviation": 1.0,
        "historical_frequency": 1.0,
        "distance_from_previous": 0.0
    }
    for k, v in defaults.items():
        if k not in txn_dict or txn_dict[k] is None:
            txn_dict[k] = v

    result = risk_engine.assess_transaction(txn_dict)
    risk_score = result.get("risk_score", 15)
    risk_level = result.get("risk_level", "LOW")
    recommendation = result.get("recommended_action", {"action": "ALLOW"})
    recommended_action_str = recommendation.get("action", "ALLOW")

    # 7. Save Transaction with First-Class Provider Column (Idempotent delivery)
    txn_data = {
        "transaction_id": common.transaction_id,
        "merchant_id": common.merchant_id,
        "amount": common.amount,
        "currency": common.currency,
        "payment_method": common.payment_method,
        "provider": common.provider,
        "customer_id": common.customer_id,
        "ip_address": common.ip,
        "status": "ALLOWED" if risk_score < 50 else ("VERIFY_REQUIRED" if risk_score < 75 else "HELD_FOR_REVIEW"),
        "timestamp": common.timestamp,
        "device_id": common.device_id,
        "location": common.location,
        **txn_dict
    }
    
    existing_txn = db.query(Transaction).filter(Transaction.transaction_id == common.transaction_id).first()
    if existing_txn:
        for k, v in txn_data.items():
            if hasattr(existing_txn, k) and v is not None:
                setattr(existing_txn, k, v)
    else:
        TransactionRepository.create_transaction(db, txn_data)
        TransactionRepository.save_risk_assessment(db, common.transaction_id, result)
        TransactionRepository.create_audit_log(db, common.transaction_id, common.merchant_id, result, txn_data)

    # 8. CRITICAL risk alert trigger
    if risk_score >= 75:
        alert = Alert(
            merchant_id=common.merchant_id,
            transaction_id=common.transaction_id,
            risk_score=risk_score,
            severity=risk_level,
            title=f"Cyber-Fraud Alert [Provider: {common.provider}]: Score {risk_score}",
            message=f"High-risk event intercepted for Invoice/Txn {common.transaction_id}.",
            created_at=datetime.now(timezone.utc)
        )
        db.add(alert)

    db.commit()

    return {
        "status": "PROCESSED",
        "provider": common.provider,
        "transaction_id": common.transaction_id,
        "risk_score": risk_score,
        "risk_level": risk_level,
        "recommended_action": recommendation,
        "risk_assessment": result
    }
