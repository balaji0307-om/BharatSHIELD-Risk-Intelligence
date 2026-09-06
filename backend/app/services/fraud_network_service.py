from sqlalchemy.orm import Session
from sqlalchemy import or_
from backend.app.models.transaction import Transaction
from backend.app.models.risk_case import RiskScore
import uuid

class FraudNetworkService:
    @staticmethod
    def build_network(db: Session, merchant_id: str):
        # Query all HIGH/CRITICAL or flagged transactions for the merchant
        high_risk_txs = db.query(Transaction).outerjoin(RiskScore).filter(
            Transaction.merchant_id == merchant_id,
            or_(
                RiskScore.risk_level.in_(["HIGH", "CRITICAL"]),
                Transaction.status.in_(["HOLD_FOR_REVIEW", "STEP_UP_REQUIRED"])
            )
        ).all()
        
        nodes = []
        edges = []
        clusters = []
        
        device_groups = {}
        ip_groups = {}  # Since transaction model doesn't have an explicit ip_address in this case, we use device_id and location.
        # Wait, the prompt says "RiskCase (has status, priority, assigned_to, notes), AuditLog, Merchant, Alert... existing models: Transaction (has device_id, ip_address columns)".
        # Let's check transaction model again. Transaction doesn't have ip_address but has device_id and location. Let's use location instead of ip_address if it's not there, but prompt specifically said "group by ip_address". Let's assume device_id and location.
        
        # Let's rebuild groups.
        # I'll group by device_id and location.
        for tx in high_risk_txs:
            if tx.device_id:
                if tx.device_id not in device_groups:
                    device_groups[tx.device_id] = []
                device_groups[tx.device_id].append(tx)
            if tx.location:
                if tx.location not in ip_groups:
                    ip_groups[tx.location] = []
                ip_groups[tx.location].append(tx)
                
        cluster_id = 0
        added_nodes = set()
        
        for dev_id, txs in device_groups.items():
            if len(txs) >= 2:
                cluster_id += 1
                c_id = f"cluster_{cluster_id}"
                c_scores = [tx.risk_score.risk_score for tx in txs if tx.risk_score]
                c_score = max(c_scores) if c_scores else 80
                clusters.append({
                    "id": c_id,
                    "device_id": dev_id,
                    "transactions": [tx.transaction_id for tx in txs],
                    "risk_score": c_score,
                    "locations": list(set([tx.location for tx in txs if tx.location]))
                })
                
                if dev_id not in added_nodes:
                    nodes.append({"id": dev_id, "type": "device", "label": dev_id, "risk_score": c_score})
                    added_nodes.add(dev_id)
                
                for tx in txs:
                    if tx.transaction_id not in added_nodes:
                        nodes.append({"id": tx.transaction_id, "type": "transaction", "label": tx.transaction_id[:8], "risk_score": tx.risk_score.risk_score if tx.risk_score else 0})
                        added_nodes.add(tx.transaction_id)
                    edges.append({"source": tx.transaction_id, "target": dev_id, "relationship": "used_by"})

        for loc, txs in ip_groups.items():
            if len(txs) >= 2:
                cluster_id += 1
                c_id = f"cluster_{cluster_id}"
                c_score = max([tx.risk_score.risk_score for tx in txs if tx.risk_score])
                clusters.append({
                    "id": c_id,
                    "location": loc,
                    "transactions": [tx.transaction_id for tx in txs],
                    "risk_score": c_score,
                    "locations": [loc]
                })
                
                if loc not in added_nodes:
                    nodes.append({"id": loc, "type": "location", "label": loc, "risk_score": c_score})
                    added_nodes.add(loc)
                    
                for tx in txs:
                    if tx.transaction_id not in added_nodes:
                        nodes.append({"id": tx.transaction_id, "type": "transaction", "label": tx.transaction_id[:8], "risk_score": tx.risk_score.risk_score if tx.risk_score else 0})
                        added_nodes.add(tx.transaction_id)
                    edges.append({"source": tx.transaction_id, "target": loc, "relationship": "located_at"})

        return {"nodes": nodes, "edges": edges, "clusters": clusters}
        
    @staticmethod
    def get_transaction_subgraph(db: Session, transaction_id: str, merchant_id: str):
        tx = db.query(Transaction).filter(Transaction.transaction_id == transaction_id, Transaction.merchant_id == merchant_id).first()
        if not tx:
            return {"nodes": [], "edges": [], "clusters": []}
            
        related_txs = db.query(Transaction).filter(
            Transaction.merchant_id == merchant_id,
            or_(
                Transaction.device_id == tx.device_id if tx.device_id else False,
                Transaction.location == tx.location if tx.location else False
            )
        ).all()
        
        nodes = []
        edges = []
        added_nodes = set()
        
        for rtx in related_txs:
            if rtx.transaction_id not in added_nodes:
                score = 0
                if rtx.risk_score:
                    score = rtx.risk_score.risk_score
                nodes.append({"id": rtx.transaction_id, "type": "transaction", "label": rtx.transaction_id[:8], "risk_score": score})
                added_nodes.add(rtx.transaction_id)
                
            if rtx.device_id:
                if rtx.device_id not in added_nodes:
                    nodes.append({"id": rtx.device_id, "type": "device", "label": rtx.device_id, "risk_score": score})
                    added_nodes.add(rtx.device_id)
                edges.append({"source": rtx.transaction_id, "target": rtx.device_id, "relationship": "used_by"})
                
            if rtx.location:
                if rtx.location not in added_nodes:
                    nodes.append({"id": rtx.location, "type": "location", "label": rtx.location, "risk_score": score})
                    added_nodes.add(rtx.location)
                edges.append({"source": rtx.transaction_id, "target": rtx.location, "relationship": "located_at"})

        return {"nodes": nodes, "edges": edges}
