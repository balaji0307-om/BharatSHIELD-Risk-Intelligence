"""
Audit API: Endpoints for paginated audit trail logs and cryptographic chain verification.
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional, List, Dict, Any

from backend.app.database.connection import get_db
from backend.app.core.security import get_current_merchant_id
from backend.app.models.risk_case import AuditLog
from backend.app.services.audit_chain_service import AuditChainService

router = APIRouter(prefix="/audit", tags=["Cryptographic Audit Trail"])

@router.get("/verify", summary="Verify Cryptographic Hash Chain Integrity")
def verify_audit_chain(
    merchant_id: str = Depends(get_current_merchant_id),
    db: Session = Depends(get_db)
):
    """
    Traverses the merchant's audit trail and verifies that every SHA-256 block
    matches its content and points correctly to the preceding block.
    """
    return AuditChainService.verify_chain(db, merchant_id)

@router.get("/logs", summary="Get Paginated Audit Logs")
def get_audit_logs(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    merchant_id: str = Depends(get_current_merchant_id),
    db: Session = Depends(get_db)
):
    offset = (page - 1) * limit
    query = db.query(AuditLog).filter(AuditLog.merchant_id == merchant_id)
    total = query.count()
    logs = query.order_by(desc(AuditLog.created_at)).offset(offset).limit(limit).all()

    items = []
    for log in logs:
        items.append({
            "log_id": log.log_id,
            "transaction_id": log.transaction_id,
            "decision_type": log.decision_type,
            "risk_score": log.risk_score,
            "risk_level": log.risk_level,
            "recommended_action": log.recommended_action,
            "reasons_summary": log.reasons_summary,
            "hash": log.hash,
            "previous_hash": log.previous_hash,
            "created_at": log.created_at.isoformat() if log.created_at else None
        })

    return {
        "page": page,
        "limit": limit,
        "total": total,
        "items": items
    }

@router.get("/logs/{log_id}", summary="Get Detailed Audit Log Block")
def get_audit_log_detail(
    log_id: str,
    merchant_id: str = Depends(get_current_merchant_id),
    db: Session = Depends(get_db)
):
    log = db.query(AuditLog).filter(
        AuditLog.log_id == log_id,
        AuditLog.merchant_id == merchant_id
    ).first()

    if not log:
        raise HTTPException(status_code=404, detail="Audit log entry not found")

    return {
        "log_id": log.log_id,
        "transaction_id": log.transaction_id,
        "decision_type": log.decision_type,
        "risk_score": log.risk_score,
        "risk_level": log.risk_level,
        "recommended_action": log.recommended_action,
        "reasons_summary": log.reasons_summary,
        "raw_payload": log.raw_payload,
        "hash": log.hash,
        "previous_hash": log.previous_hash,
        "created_at": log.created_at.isoformat() if log.created_at else None
    }
