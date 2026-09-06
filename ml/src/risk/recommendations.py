"""
Module for generating transaction recommendations based on risk levels.
"""

from typing import Optional, List, Dict, Any
from .thresholds import RiskLevel

__all__ = ["get_recommendation"]

def get_recommendation(risk_level: RiskLevel, risk_factors: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    """
    Map risk levels to recommended actions and contextual details.
    
    Args:
        risk_level: The evaluated RiskLevel.
        risk_factors: Optional list of dictionaries describing specific risk factors.
        
    Returns:
        A dictionary containing recommendation action, description, urgency, and details.
    """
    details = []
    if risk_factors:
        for factor in risk_factors:
            name = factor.get("name", "Unknown Factor")
            desc = factor.get("description", "")
            details.append(f"{name}: {desc}")

    if risk_level == RiskLevel.LOW:
        return {
            "action": "Allow",
            "description": "Auto-approve and standard monitoring.",
            "urgency": "Low",
            "details": details or ["No significant risk factors identified."]
        }
    elif risk_level == RiskLevel.MEDIUM:
        return {
            "action": "Verify",
            "description": "Additional verification, OTP/2FA recommended.",
            "urgency": "Medium",
            "details": details or ["Elevated risk detected, verify user identity."]
        }
    elif risk_level == RiskLevel.HIGH:
        return {
            "action": "Step-up Auth",
            "description": "Enhanced authentication, route to manual review queue.",
            "urgency": "High",
            "details": details or ["High risk score suggests potential fraud, review required."]
        }
    elif risk_level == RiskLevel.CRITICAL:
        return {
            "action": "Hold for Review",
            "description": "Block transaction immediately and alert risk team.",
            "urgency": "Critical",
            "details": details or ["Critical risk factors present, immediate action required."]
        }
        
    # Fallback
    return {
        "action": "Unknown",
        "description": "Unable to determine recommendation.",
        "urgency": "Unknown",
        "details": details
    }
