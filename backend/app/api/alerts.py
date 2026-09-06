"""
Alerts API endpoints: fraud spike detection, velocity anomaly monitoring, and acknowledgment.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.database.connection import get_db
from backend.app.core.security import get_current_merchant_id
from backend.app.schemas.alert import AlertOut, AlertAcknowledgeRequest
from backend.app.database.repositories import AlertRepository
from backend.app.services.anomaly_service import AnomalyService

router = APIRouter(prefix="/alerts", tags=["Alerts & Anomalies"])
anomaly_service = AnomalyService()

@router.get("", response_model=List[AlertOut], summary="List Active & Historical Alerts")
def list_alerts(
    merchant_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_merchant: str = Depends(get_current_merchant_id)
):
    effective_merchant = merchant_id or current_merchant
    alerts = AlertRepository.list_alerts(db, merchant_id=effective_merchant)
    return alerts

@router.put("/{alert_id}/acknowledge", response_model=AlertOut, summary="Acknowledge Alert")
def acknowledge_alert(
    alert_id: str,
    payload: Optional[AlertAcknowledgeRequest] = None,
    db: Session = Depends(get_db)
):
    alert = AlertRepository.acknowledge_alert(db, alert_id=alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found.")
    return alert

@router.post("/check-spikes", summary="Trigger Manual Anomaly Check")
def check_spikes(
    merchant_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_merchant: str = Depends(get_current_merchant_id)
):
    effective_merchant = merchant_id or current_merchant
    alert = anomaly_service.evaluate_merchant_spikes(db, merchant_id=effective_merchant)
    if alert:
        return {"status": "SPIKE_TRIGGERED", "alert_id": alert.alert_id, "title": alert.title}
    return {"status": "NORMAL", "message": "Transaction volume and risk ratios are within normal baseline limits."}
