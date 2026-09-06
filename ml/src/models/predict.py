"""
Prediction module for BharatSHIELD.
"""
import joblib
import pandas as pd
import numpy as np
from typing import Dict, Any, Union

try:
    from risk.scoring import calculate_risk_score
    from risk.thresholds import determine_risk_level
    from risk.recommendations import get_recommendation
except ImportError:
    def calculate_risk_score(prob): return prob * 100
    def determine_risk_level(score): return "HIGH" if score > 80 else ("MEDIUM" if score > 40 else "LOW")
    def get_recommendation(level): return "BLOCK" if level == "HIGH" else "ALLOW"

def load_model(model_path: str) -> Any:
    """Load serialized model."""
    return joblib.load(model_path)

def predict_fraud_probability(model: Any, features: Union[Dict, pd.DataFrame]) -> Union[float, np.ndarray]:
    """Predict the probability of fraud."""
    if isinstance(features, dict):
        df = pd.DataFrame([features])
    else:
        df = features
        
    probabilities = model.predict_proba(df)[:, 1]
    
    if isinstance(features, dict):
        return float(probabilities[0])
    return probabilities

def predict_single(model: Any, features: Dict, feature_order: list = None) -> Dict[str, Any]:
    """Predict risk for a single transaction and return actionable insights."""
    if feature_order:
        features_ordered = {k: features.get(k, 0) for k in feature_order}
        df = pd.DataFrame([features_ordered])
    else:
        df = pd.DataFrame([features])
        
    prob = predict_fraud_probability(model, df)
    score = calculate_risk_score(prob)
    level = determine_risk_level(score)
    rec = get_recommendation(level)
    
    return {
        "probability": prob,
        "risk_score": score,
        "risk_level": level,
        "recommendation": rec
    }
