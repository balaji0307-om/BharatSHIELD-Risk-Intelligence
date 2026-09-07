"""
Explainability module using SHAP for BharatSHIELD.
"""
import logging
import shap
import numpy as np
import pandas as pd
from typing import Dict, Any, Union

logger = logging.getLogger(__name__)

class FraudExplainer:
    def __init__(self, model: Any, feature_names: list):
        self.model = model
        self.feature_names = feature_names
        
        try:
            self.explainer = shap.TreeExplainer(model)
        except Exception as exc:
            logger.warning(f"TreeExplainer initialization failed: {exc}")
            self.explainer = None
            
        self._feature_display_names = {
            "is_new_device": "New Device Detected",
            "transaction_amount": "Transaction Amount",
            "transactions_last_5min": "Transaction Velocity (5 min)",
            "distance_from_previous": "Distance from Previous Transaction",
            "failed_attempts": "Failed Authentication Attempts",
            "device_age_days": "Device Age",
            "amount_deviation": "Amount Deviation from Average",
            "is_new_location": "New Location Detected"
        }

    def explain_prediction(self, features: Union[Dict, np.ndarray]) -> Dict[str, Any]:
        """Explain a single prediction."""
        if isinstance(features, dict):
            df = pd.DataFrame([features])
            feature_vals = features
        else:
            df = pd.DataFrame(features, columns=self.feature_names)
            feature_vals = df.iloc[0].to_dict()
            
        if self.explainer:
            shap_values = self.explainer.shap_values(df)
            if isinstance(shap_values, list):
                shap_values = shap_values[1]
            if len(shap_values.shape) > 1:
                shap_vals = shap_values[0]
            else:
                shap_vals = shap_values
                
            expected_value = self.explainer.expected_value
            if isinstance(expected_value, (list, np.ndarray)):
                expected_value = expected_value[-1]
        else:
            shap_vals = np.zeros(len(self.feature_names))
            expected_value = 0.0
            
        risk_factors = []
        for i, feat in enumerate(self.feature_names):
            val = shap_vals[i]
            if val != 0:
                risk_factors.append({
                    "feature": feat,
                    "display_name": self._feature_display_names.get(feat, feat),
                    "contribution": float(abs(val)),
                    "direction": "increases_risk" if val > 0 else "decreases_risk",
                    "value": feature_vals.get(feat, None)
                })
                
        risk_factors = sorted(risk_factors, key=lambda x: x["contribution"], reverse=True)
        
        base_risk_score = float(expected_value) * 10
        total_risk_adjustment = float(sum(np.abs(shap_vals))) * 10
        
        return {
            "shap_values": shap_vals.tolist(),
            "risk_factors": risk_factors,
            "base_risk_score": base_risk_score,
            "total_risk_adjustment": total_risk_adjustment
        }
