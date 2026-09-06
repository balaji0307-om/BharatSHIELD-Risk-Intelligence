"""
Recommendation service mapping risk score, risk level, and SHAP factors to actionable protocols.
"""

from typing import Dict, Any, List, Optional
from ml.src.risk.thresholds import RiskLevel

def generate_recommendation(risk_level: str, risk_factors: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    """
    Generates structured recommended action with specific domain reasoning.
    """
    level_str = risk_level.upper()
    
    details: List[str] = []
    if risk_factors:
        for factor in risk_factors[:3]:
            feat = factor.get("display_name", factor.get("feature", "Factor"))
            pts = factor.get("contribution", 0.0)
            direction = factor.get("direction", "increases_risk")
            if direction == "increases_risk" and pts > 0:
                details.append(f"{feat} added ~{pts:.1f} risk impact")
                
    if level_str == RiskLevel.LOW.value:
        return {
            "action": "Allow Transaction",
            "description": "Risk profile is nominal. Clear transaction through straight-through processing (STP).",
            "urgency": "LOW",
            "details": details or ["Standard fraud indicators within baseline safety margins."]
        }
    elif level_str == RiskLevel.MEDIUM.value:
        return {
            "action": "Verify Credentials",
            "description": "Moderate deviation detected. Trigger silent device verification or passive biometric challenge.",
            "urgency": "MEDIUM",
            "details": details or ["Subtle velocity or location deviation observed."]
        }
    elif level_str == RiskLevel.HIGH.value:
        return {
            "action": "Mandate Step-Up Auth",
            "description": "Substantial risk signals identified. Challenge user with 2-Factor Authentication (OTP/Passkey).",
            "urgency": "HIGH",
            "details": details or ["Multiple anomalous factors exceed security thresholds."]
        }
    else:  # CRITICAL
        return {
            "action": "Hold for Review",
            "description": "Critical fraud probability! Freeze funds settlement, alert security analyst, and queue for manual audit.",
            "urgency": "CRITICAL",
            "details": details or ["Critical attack pattern detected across velocity and device credentials."]
        }
