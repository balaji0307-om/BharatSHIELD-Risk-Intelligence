"""
Database seed script: populates merchants, demo transactions, risk scores, SHAP factors,
audit logs, and fraud spike alerts.

Usage:
    python scripts/seed_database.py
"""

import os
import sys
from pathlib import Path
import pandas as pd
from datetime import datetime, timezone

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.database.connection import init_db, SessionLocal
from backend.app.models.transaction import Merchant, Transaction
from backend.app.models.risk_case import RiskScore, RiskFactor, AuditLog
from backend.app.services.risk_engine import risk_engine
from backend.app.services.anomaly_service import AnomalyService
from backend.app.database.repositories import TransactionRepository

def seed():
    print("=" * 60)
    print("  BharatSHIELD - Database Seeding Pipeline")
    print("=" * 60)
    
    print("\n[1] Initializing database schema...")
    init_db()
    db = SessionLocal()
    
    # 1. Seed Merchants
    print("\n[2] Seeding merchant registry...")
    merchants = [
        {"merchant_id": "MER_razorpay_001", "name": "Razorpay Prime Merchant", "api_key": "key_live_razorpay_001_secret"},
        {"merchant_id": "MER_phonepe_002", "name": "PhonePe Enterprise Merchant", "api_key": "key_live_phonepe_002_secret"},
        {"merchant_id": "MER_paytm_001", "name": "Paytm Merchant Solutions", "api_key": "key_live_paytm_001_secret"},
        {"merchant_id": "MER_bharatpe_001", "name": "BharatPe Retail Outlet", "api_key": "key_live_bharatpe_001_secret"},
    ]
    
    for m in merchants:
        existing = db.query(Merchant).filter(Merchant.merchant_id == m["merchant_id"]).first()
        if not existing:
            db.add(Merchant(**m))
    db.commit()
    print(f"  Seeded {len(merchants)} merchants.")

    # 2. Load demo transactions
    demo_csv = PROJECT_ROOT / "data" / "raw" / "demo_transactions.csv"
    if not demo_csv.exists():
        print("  demo_transactions.csv not found, generating now...")
        from scripts.generate_demo_data import generate_transactions
        df = generate_transactions(num_transactions=1000)
    else:
        df = pd.read_csv(demo_csv)

    print(f"\n[3] Scoring and seeding {len(df)} transactions through Risk Engine...")
    
    # Ensure risk engine artifacts are loaded
    risk_engine.load_artifacts()
    
    seeded_txns = 0
    fraud_count = 0
    
    for idx, row in df.iterrows():
        raw_dict = row.to_dict()
        txn_id = str(raw_dict.get("transaction_id", f"txn_seed_{idx}"))
        raw_dict["transaction_id"] = txn_id
        
        # Check if already seeded
        if db.query(Transaction).filter(Transaction.transaction_id == txn_id).first():
            continue
            
        # Parse timestamp
        ts_val = raw_dict.get("timestamp")
        if isinstance(ts_val, str):
            try:
                raw_dict["timestamp"] = datetime.fromisoformat(ts_val)
            except Exception:
                raw_dict["timestamp"] = datetime.now(timezone.utc)
        else:
            raw_dict["timestamp"] = datetime.now(timezone.utc)

        # Run risk assessment
        assessment = risk_engine.assess_transaction(raw_dict)
        
        # Determine status
        level = assessment["risk_level"]
        if level == "LOW":
            txn_status = "ALLOWED"
        elif level == "MEDIUM":
            txn_status = "VERIFY_REQUIRED"
        elif level == "HIGH":
            txn_status = "STEP_UP_REQUIRED"
        else:
            txn_status = "HOLD_FOR_REVIEW"
            fraud_count += 1
            
        raw_dict["status"] = txn_status
        
        # Persist transaction
        TransactionRepository.create_transaction(db, raw_dict)
        
        # Persist risk score & factors
        TransactionRepository.save_risk_assessment(db, txn_id, assessment)
        
        # Write immutable audit log
        TransactionRepository.create_audit_log(db, txn_id, raw_dict.get("merchant_id", "MER_razorpay_001"), assessment, raw_dict)
        
        seeded_txns += 1
        if seeded_txns % 50 == 0:
            db.commit()
            print(f"  Processed {seeded_txns}/{len(df)} transactions...")
            
    db.commit()
    print(f"\n  Successfully seeded {seeded_txns} transactions ({fraud_count} flagged as CRITICAL).")

    # 3. Trigger Anomaly Spike Detection
    print("\n[4] Evaluating merchant volume and fraud ratios for anomaly spikes...")
    anomaly_service = AnomalyService()
    for m in merchants:
        alert = anomaly_service.evaluate_merchant_spikes(db, m["merchant_id"])
        if alert:
            print(f"  [ALERT CREATED] {alert.title} for {m['merchant_id']} (Severity: {alert.severity})")
            
    db.close()
    print("\n" + "=" * 60)
    print("  Database Seeding Completed Successfully!")
    print("=" * 60)

if __name__ == "__main__":
    seed()
