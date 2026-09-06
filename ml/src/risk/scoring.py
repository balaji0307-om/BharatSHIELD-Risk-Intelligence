"""
Module for calculating risk scores from fraud probabilities.
"""

import numpy as np

__all__ = ["probability_to_risk_score", "batch_risk_scores"]

def probability_to_risk_score(probability: float, k: float = 10.0, threshold: float = 0.5) -> int:
    """
    Convert fraud probability (0-1) to risk score (0-100) using calibrated sigmoid scaling.
    
    Args:
        probability: Fraud probability between 0 and 1.
        k: Controls steepness of the sigmoid curve.
        threshold: The decision boundary probability.
        
    Returns:
        Risk score as an integer between 0 and 100.
    """
    if probability is None or np.isnan(probability):
        return 0
    probability = max(0.0, min(1.0, probability))
    # Score = 100 * (1 / (1 + exp(-k * (prob - threshold))))
    score_float = 100 * (1 / (1 + np.exp(-k * (probability - threshold))))
    return int(round(score_float))

def batch_risk_scores(probabilities: np.ndarray, k: float = 10.0, threshold: float = 0.5) -> np.ndarray:
    """
    Vectorized version of probability_to_risk_score for numpy arrays.
    
    Args:
        probabilities: Array of fraud probabilities between 0 and 1.
        k: Controls steepness of the sigmoid curve.
        threshold: The decision boundary probability.
        
    Returns:
        Array of risk scores as integers between 0 and 100.
    """
    if probabilities is None or len(probabilities) == 0:
        return np.array([])
        
    probabilities = np.clip(probabilities, 0.0, 1.0)
    scores = 100 * (1 / (1 + np.exp(-k * (probabilities - threshold))))
    return np.round(scores).astype(int)
