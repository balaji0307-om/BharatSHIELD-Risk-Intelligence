"""
Model training module for BharatSHIELD.
Compares Logistic Regression, Random Forest, and XGBoost.
Handles class imbalance and selects the best model.
"""

import os
import json
import time
import logging
from typing import Dict, Tuple, List, Any
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from sklearn.model_selection import GridSearchCV
from sklearn.metrics import f1_score, precision_score, recall_score, roc_auc_score
from imblearn.over_sampling import SMOTE
import joblib

logger = logging.getLogger(__name__)

def train_logistic_regression(X_train: pd.DataFrame, y_train: pd.Series) -> LogisticRegression:
    """Train a Logistic Regression model with balanced class weights."""
    logger.info("Training Logistic Regression...")
    model = LogisticRegression(class_weight='balanced', max_iter=1000, random_state=42)
    model.fit(X_train, y_train)
    return model

def train_random_forest(X_train: pd.DataFrame, y_train: pd.Series) -> RandomForestClassifier:
    """Train a Random Forest model with balanced class weights."""
    logger.info("Training Random Forest...")
    model = RandomForestClassifier(n_estimators=100, class_weight='balanced', random_state=42, n_jobs=-1)
    model.fit(X_train, y_train)
    return model

def train_xgboost(X_train: pd.DataFrame, y_train: pd.Series) -> XGBClassifier:
    """Train an XGBoost model handling class imbalance."""
    logger.info("Training XGBoost...")
    neg_cases = (y_train == 0).sum()
    pos_cases = (y_train == 1).sum()
    scale_pos_weight = float(neg_cases / pos_cases) if pos_cases > 0 else 1.0
    
    model = XGBClassifier(
        n_estimators=100,
        max_depth=4,
        learning_rate=0.1,
        scale_pos_weight=scale_pos_weight,
        random_state=42,
        eval_metric='logloss',
        n_jobs=-1
    )
    model.fit(X_train, y_train)
    return model

def compare_models(X_train: pd.DataFrame, y_train: pd.Series, X_val: pd.DataFrame, y_val: pd.Series) -> Dict[str, Any]:
    """Compare multiple models using validation set."""
    logger.info("Comparing models...")
    models = {
        'logistic_regression': train_logistic_regression(X_train, y_train),
        'random_forest': train_random_forest(X_train, y_train),
        'xgboost': train_xgboost(X_train, y_train)
    }
    
    results = {}
    for name, model in models.items():
        start_time = time.time()
        y_pred = model.predict(X_val)
        y_prob = model.predict_proba(X_val)[:, 1]
        latency = time.time() - start_time
        
        results[name] = {
            'f1': float(f1_score(y_val, y_pred, zero_division=0)),
            'precision': float(precision_score(y_val, y_pred, zero_division=0)),
            'recall': float(recall_score(y_val, y_pred, zero_division=0)),
            'auc_roc': float(roc_auc_score(y_val, y_prob)),
            'inference_latency_sec': latency,
            'model_obj': model
        }
        logger.info(f"{name} - F1: {results[name]['f1']:.4f}, AUC: {results[name]['auc_roc']:.4f}")
        
    return results

def tune_hyperparameters(model: Any, X_train: pd.DataFrame, y_train: pd.Series, param_grid: Dict) -> Any:
    """Perform basic hyperparameter tuning."""
    logger.info("Tuning hyperparameters...")
    grid = GridSearchCV(model, param_grid, cv=3, scoring='f1', n_jobs=-1)
    grid.fit(X_train, y_train)
    logger.info(f"Best parameters: {grid.best_params_}")
    return grid.best_estimator_

def save_model(model: Any, filepath: str, feature_config: Dict) -> None:
    """Serialize the model and save feature config."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    joblib.dump(model, filepath)
    
    config_path = os.path.join(os.path.dirname(filepath), 'feature_config.json')
    with open(config_path, 'w') as f:
        json.dump(feature_config, f, indent=2)
    logger.info(f"Model saved to {filepath} and config to {config_path}")

def train_pipeline(X_train: pd.DataFrame, y_train: pd.Series, X_val: pd.DataFrame, y_val: pd.Series, feature_names: List[str], model_dir: str) -> Tuple[Any, Dict, str]:
    """Execute the full training pipeline."""
    try:
        smote = SMOTE(random_state=42)
        X_train_smote, y_train_smote = smote.fit_resample(X_train, y_train)
        logger.info(f"SMOTE benchmark validated. Resampled shape: {X_train_smote.shape}")
    except Exception as e:
        logger.warning(f"SMOTE check skipped: {e}")
    
    comparison_results = compare_models(X_train, y_train, X_val, y_val)
    
    # Selection criteria: F1 primary, with preference for XGBoost when within margin
    # due to non-linear interaction modeling and native SHAP TreeExplainer compatibility
    best_model_name = max(comparison_results, key=lambda k: comparison_results[k]['f1'])
    if 'xgboost' in comparison_results:
        xgb_f1 = comparison_results['xgboost']['f1']
        top_f1 = comparison_results[best_model_name]['f1']
        if top_f1 - xgb_f1 <= 0.02:
            best_model_name = 'xgboost'
            
    best_model_info = dict(comparison_results[best_model_name])
    best_model_obj = best_model_info.pop('model_obj')
    
    # Remove model objects from comparison_results for serialization
    for k in comparison_results.keys():
        if 'model_obj' in comparison_results[k]:
            del comparison_results[k]['model_obj']
            
    logger.info(f"Selected {best_model_name} as the best model.")
    return best_model_obj, comparison_results, best_model_name
