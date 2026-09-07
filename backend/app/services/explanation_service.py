"""
Explanation service wrapping SHAP TreeExplainer and human-readable translation.
"""

import logging
from typing import Dict, Any, List
import pandas as pd
from ml.src.explainability.explainer import FraudExplainer

logger = logging.getLogger(__name__)

class ExplanationService:
    def __init__(self, explainer: FraudExplainer):
        self.explainer = explainer

    def get_explanation(self, feature_dict: Dict[str, Any], feature_vector: pd.DataFrame) -> Dict[str, Any]:
        """
        Produces ranked risk factors, base risk, and directional impacts.
        """
        if self.explainer is None:
            return {
                "risk_factors": [],
                "base_risk_score": 10.0,
                "total_risk_adjustment": 0.0
            }
        
        try:
            raw_exp = self.explainer.explain_prediction(feature_vector)
            return raw_exp
        except Exception as exc:
            logger.warning(f"SHAP TreeExplainer failed, falling back to heuristic explanation: {exc}", exc_info=True)
            return self._heuristic_explanation(feature_dict)

    def _heuristic_explanation(self, feat: Dict[str, Any]) -> Dict[str, Any]:
        factors = []
        if feat.get("is_new_device"):
            factors.append({
                "feature": "is_new_device",
                "display_name": "New Device Detected",
                "contribution": 28.5,
                "direction": "increases_risk",
                "value": True
            })
        if feat.get("failed_attempts", 0) >= 2:
            factors.append({
                "feature": "failed_attempts",
                "display_name": "Failed Authentication Attempts",
                "contribution": 22.0 * feat.get("failed_attempts", 1),
                "direction": "increases_risk",
                "value": feat.get("failed_attempts")
            })
        if feat.get("transactions_last_5min", 0) > 3:
            factors.append({
                "feature": "transactions_last_5min",
                "display_name": "High Transaction Velocity (5 min)",
                "contribution": 25.0,
                "direction": "increases_risk",
                "value": feat.get("transactions_last_5min")
            })
        if feat.get("distance_from_previous", 0) > 100:
            factors.append({
                "feature": "distance_from_previous",
                "display_name": "Impossible Travel Distance",
                "contribution": 30.0,
                "direction": "increases_risk",
                "value": feat.get("distance_from_previous")
            })
        if feat.get("amount_deviation", 1.0) > 3.0:
            factors.append({
                "feature": "amount_deviation",
                "display_name": "Anomalous Amount vs Historical",
                "contribution": 18.5,
                "direction": "increases_risk",
                "value": feat.get("amount_deviation")
            })
            
        return {
            "risk_factors": factors,
            "base_risk_score": 10.0,
            "total_risk_adjustment": sum(f["contribution"] for f in factors)
        }
