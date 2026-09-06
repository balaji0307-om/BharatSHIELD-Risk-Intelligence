from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.app.database.connection import get_db
from backend.app.core.security import get_current_merchant_id
from backend.app.services.fraud_network_service import FraudNetworkService

router = APIRouter(prefix="/fraud-network", tags=["Fraud Network"])

@router.get("") 
def get_fraud_network(merchant_id: str = Depends(get_current_merchant_id), db: Session = Depends(get_db)):
    return FraudNetworkService.build_network(db, merchant_id)

@router.get("/{transaction_id}")
def get_transaction_network(transaction_id: str, merchant_id: str = Depends(get_current_merchant_id), db: Session = Depends(get_db)):
    return FraudNetworkService.get_transaction_subgraph(db, transaction_id, merchant_id)
