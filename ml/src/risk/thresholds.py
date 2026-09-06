"""
Module defining risk levels, thresholds, and presentation utilities.
"""

from enum import Enum

__all__ = ["RiskLevel", "RISK_BANDS", "get_risk_level", "get_risk_color", "get_risk_description"]

class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

RISK_BANDS = {
    RiskLevel.LOW: (0, 24),
    RiskLevel.MEDIUM: (25, 49),
    RiskLevel.HIGH: (50, 74),
    RiskLevel.CRITICAL: (75, 100),
}

def get_risk_level(score: int) -> RiskLevel:
    """
    Get the risk level corresponding to a 0-100 risk score.
    
    Args:
        score: Risk score between 0 and 100.
        
    Returns:
        RiskLevel enum value.
    """
    if score is None:
        return RiskLevel.LOW
        
    # Clamp score
    score = max(0, min(100, score))
    
    for level, (min_val, max_val) in RISK_BANDS.items():
        if min_val <= score <= max_val:
            return level
            
    return RiskLevel.CRITICAL

def get_risk_color(level: RiskLevel) -> str:
    """
    Get the hex color code associated with a risk level.
    
    Args:
        level: RiskLevel enum value.
        
    Returns:
        Hex color code as a string.
    """
    colors = {
        RiskLevel.LOW: "#4CAF50",       # Green
        RiskLevel.MEDIUM: "#FF9800",    # Orange
        RiskLevel.HIGH: "#F44336",      # Red
        RiskLevel.CRITICAL: "#B71C1C",  # Dark Red
    }
    return colors.get(level, "#9E9E9E")

def get_risk_description(level: RiskLevel) -> str:
    """
    Get a human-readable description for a risk level.
    
    Args:
        level: RiskLevel enum value.
        
    Returns:
        Description string.
    """
    descriptions = {
        RiskLevel.LOW: "Low risk transaction. Normal processing.",
        RiskLevel.MEDIUM: "Medium risk transaction. Additional verification may be needed.",
        RiskLevel.HIGH: "High risk transaction. Requires step-up authentication or manual review.",
        RiskLevel.CRITICAL: "Critical risk transaction. Immediate hold and alert recommended.",
    }
    return descriptions.get(level, "Unknown risk level.")
