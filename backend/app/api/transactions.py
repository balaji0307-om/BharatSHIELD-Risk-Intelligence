"""
Transaction API endpoints: scoring, listing, deep-dive inspection, and related activity linking.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.database.connection import get_db
from backend.app.core.security import get_current_merchant_id
from backend.app.schemas.transaction import (
    TransactionScoreRequest,
    TransactionScoreResponse,
    TransactionListResponse
)
from backend.app.services.transaction_service import TransactionService
from backend.app.database.repositories import TransactionRepository

router = APIRouter(prefix="/transactions", tags=["Transactions"])

@router.post("/score", response_model=TransactionScoreResponse, summary="Score & Process Transaction")
def score_transaction(
    payload: TransactionScoreRequest,
    db: Session = Depends(get_db),
    current_merchant: str = Depends(get_current_merchant_id)
):
    """
    Submits a transaction to BharatSHIELD's Risk Engine.
    Executes XGBoost inference, computes SHAP attributions, maps risk band,
    persists audit log, and returns real-time risk intelligence.
    """
    # Override merchant_id if specified in authenticated session
    if current_merchant and not payload.merchant_id:
        payload.merchant_id = current_merchant
        
    result = TransactionService.process_and_score(db, payload)
    return result

@router.get("", response_model=TransactionListResponse, summary="List Transactions")
def list_transactions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    risk_level: Optional[str] = Query(None, description="Filter by risk band: LOW, MEDIUM, HIGH, CRITICAL"),
    merchant_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_merchant: str = Depends(get_current_merchant_id)
):
    effective_merchant = merchant_id or current_merchant
    items, total = TransactionRepository.list_transactions(
        db, merchant_id=effective_merchant, risk_level=risk_level, page=page, page_size=page_size
    )
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages
    }

@router.get("/{transaction_id}", summary="Get Single Transaction Deep Dive")
def get_transaction(
    transaction_id: str,
    db: Session = Depends(get_db)
):
    details = TransactionRepository.get_transaction_details(db, transaction_id)
    if not details:
        raise HTTPException(status_code=404, detail="Transaction not found.")
    return details

@router.get("/{transaction_id}/related", summary="Get Related Transactions")
def get_related_transactions(
    transaction_id: str,
    db: Session = Depends(get_db)
):
    related = TransactionRepository.get_related_transactions(db, transaction_id)
    return {"transaction_id": transaction_id, "related_transactions": related}
