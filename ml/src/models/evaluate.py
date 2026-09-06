"""
Evaluation module for BharatSHIELD.
"""
import json
import numpy as np
import pandas as pd
from typing import Dict, Any
from sklearn.metrics import (
    precision_score, recall_score, f1_score, accuracy_score,
    roc_auc_score, average_precision_score, confusion_matrix,
    classification_report
)

def evaluate_model(model: Any, X_test: pd.DataFrame, y_test: pd.Series, threshold: float = 0.5) -> Dict[str, Any]:
    """Evaluate model and return comprehensive metrics."""
    y_prob = model.predict_proba(X_test)[:, 1]
    y_pred = (y_prob >= threshold).astype(int)
    
    cm = confusion_matrix(y_test, y_pred)
    tn, fp, fn, tp = cm.ravel()
    
    metrics = {
        "precision": float(precision_score(y_test, y_pred, zero_division=0)),
        "recall": float(recall_score(y_test, y_pred)),
        "f1_score": float(f1_score(y_test, y_pred)),
        "accuracy": float(accuracy_score(y_test, y_pred)),
        "auc_roc": float(roc_auc_score(y_test, y_prob)),
        "auc_pr": float(average_precision_score(y_test, y_prob)),
        "false_positive_rate": float(fp / (fp + tn)) if (fp + tn) > 0 else 0.0,
        "false_negative_rate": float(fn / (fn + tp)) if (fn + tp) > 0 else 0.0,
        "confusion_matrix": cm.tolist(),
        "classification_report": classification_report(y_test, y_pred),
        "fraud_detection_rate": float(tp / (tp + fn)) if (tp + fn) > 0 else 0.0,
        "false_alarm_rate": float(fp / (fp + tn)) if (fp + tn) > 0 else 0.0
    }
    return metrics

def find_optimal_threshold(model: Any, X_val: pd.DataFrame, y_val: pd.Series, metric: str = 'f1') -> float:
    """Sweep thresholds 0.1-0.9 to find optimal threshold."""
    y_prob = model.predict_proba(X_val)[:, 1]
    thresholds = np.arange(0.1, 1.0, 0.05)
    best_threshold = 0.5
    best_score = -1.0
    
    for th in thresholds:
        y_pred = (y_prob >= th).astype(int)
        if metric == 'f1':
            score = f1_score(y_val, y_pred)
        elif metric == 'precision':
            score = precision_score(y_val, y_pred, zero_division=0)
        elif metric == 'recall':
            score = recall_score(y_val, y_pred)
        else:
            raise ValueError(f"Unsupported metric: {metric}")
            
        if score > best_score:
            best_score = score
            best_threshold = th
            
    return float(best_threshold)

def save_evaluation_report(metrics: Dict[str, Any], filepath: str) -> None:
    """Save evaluation metrics as JSON."""
    with open(filepath, 'w') as f:
        json.dump(metrics, f, indent=2)
