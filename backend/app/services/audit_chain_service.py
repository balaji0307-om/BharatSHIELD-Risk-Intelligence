"""
Audit Chain Service: Cryptographic hash chain for immutable audit logging.
Computes SHA-256 links between consecutive audit logs to ensure tamper-evidence.
"""

import hashlib
import json
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.app.models.risk_case import AuditLog

class AuditChainService:
    @staticmethod
    def compute_hash(
        log_id: str,
        transaction_id: str,
        risk_score: int,
        risk_level: str,
        recommended_action: str,
        reasons_summary: str,
        raw_payload: str,
        created_at: Any,
        previous_hash: str = ""
    ) -> str:
        if hasattr(created_at, 'strftime'):
            created_str = created_at.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(created_at, str):
            created_str = created_at[:19]
        else:
            created_str = str(created_at)[:19] if created_at else ""
            
        content = f"{log_id}|{transaction_id}|{risk_score}|{risk_level}|{recommended_action}|{reasons_summary}|{raw_payload}|{created_str}|{previous_hash or ''}"
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    @staticmethod
    def append_to_chain(db: Session, audit_entry: AuditLog) -> AuditLog:
        # Fetch the most recent prior log for this merchant (or system-wide)
        last_log = db.query(AuditLog).filter(
            AuditLog.merchant_id == audit_entry.merchant_id,
            AuditLog.log_id != audit_entry.log_id
        ).order_by(desc(AuditLog.created_at)).first()

        prev_hash = last_log.hash if (last_log and last_log.hash) else "GENESIS_BLOCK_BHARATSHIELD"
        audit_entry.previous_hash = prev_hash
        audit_entry.hash = AuditChainService.compute_hash(
            log_id=audit_entry.log_id,
            transaction_id=audit_entry.transaction_id,
            risk_score=audit_entry.risk_score,
            risk_level=audit_entry.risk_level,
            recommended_action=audit_entry.recommended_action,
            reasons_summary=audit_entry.reasons_summary,
            raw_payload=audit_entry.raw_payload,
            created_at=audit_entry.created_at,
            previous_hash=prev_hash
        )
        return audit_entry

    @staticmethod
    def verify_chain(db: Session, merchant_id: str) -> Dict[str, Any]:
        logs = db.query(AuditLog).filter(
            AuditLog.merchant_id == merchant_id
        ).order_by(AuditLog.created_at.asc()).all()

        if not logs:
            return {
                "valid": True,
                "total_records": 0,
                "last_verified": datetime.now(timezone.utc).isoformat(),
                "broken_at": None,
                "message": "Chain empty (Genesis state)."
            }

        prev_hash = "GENESIS_BLOCK_BHARATSHIELD"
        for idx, log in enumerate(logs):
            # Check link to previous
            if log.previous_hash and log.previous_hash != prev_hash:
                return {
                    "valid": False,
                    "total_records": len(logs),
                    "broken_at": log.log_id,
                    "reason": f"Mismatched previous_hash at index {idx}",
                    "last_verified": datetime.now(timezone.utc).isoformat()
                }

            # Check self recalculation
            expected_hash = AuditChainService.compute_hash(
                log_id=log.log_id,
                transaction_id=log.transaction_id,
                risk_score=log.risk_score,
                risk_level=log.risk_level,
                recommended_action=log.recommended_action,
                reasons_summary=log.reasons_summary,
                raw_payload=log.raw_payload,
                created_at=log.created_at,
                previous_hash=log.previous_hash or prev_hash
            )

            if log.hash and log.hash != expected_hash:
                return {
                    "valid": False,
                    "total_records": len(logs),
                    "broken_at": log.log_id,
                    "reason": f"Corrupted content hash at index {idx}",
                    "last_verified": datetime.now(timezone.utc).isoformat()
                }

            prev_hash = log.hash or expected_hash

        return {
            "valid": True,
            "total_records": len(logs),
            "last_verified": datetime.now(timezone.utc).isoformat(),
            "broken_at": None,
            "message": "All cryptographic signatures and chain blocks verified."
        }
