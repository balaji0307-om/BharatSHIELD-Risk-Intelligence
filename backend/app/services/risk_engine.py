"""
Risk Engine Orchestrator: Combines ML inference, SHAP explainability, and policy recommendations.
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional
import joblib
import numpy as np
import pandas as pd

from backend.app.core.config import settings
from ml.src.risk.scoring import probability_to_risk_score
from ml.src.risk.thresholds import get_risk_level, RiskLevel
from backend.app.services.recommendation_service import generate_recommendation
from backend.app.services.explanation_service import ExplanationService
from ml.src.explainability.explainer import FraudExplainer
from ml.src.features.transaction_features import engineer_transaction_features
from ml.src.features.velocity_features import engineer_velocity_features
from ml.src.features.behavioural_features import engineer_behavioural_features

logger = logging.getLogger(__name__)

class RiskEngine:
    def __init__(self):
        self.model = None
        self.scaler = None
        self.feature_names: List[str] = []
        self.feature_config: Dict[str, Any] = {}
        self.explainer: Optional[FraudExplainer] = None
        self.explanation_service: Optional[ExplanationService] = None
        self.optimal_threshold: float = 0.5
        
        self.load_artifacts()

    def load_artifacts(self):
        """Loads serialized XGBoost model, Scaler transformer, and feature config."""
        try:
            if os.path.exists(settings.MODEL_PATH):
                self.model = joblib.load(settings.MODEL_PATH)
                logger.info(f"Loaded ML model from {settings.MODEL_PATH}")
            else:
                logger.warning(f"Model path {settings.MODEL_PATH} not found.")

            if os.path.exists(settings.SCALER_PATH):
                self.scaler = joblib.load(settings.SCALER_PATH)
                logger.info(f"Loaded Scaler from {settings.SCALER_PATH}")

            if os.path.exists(settings.FEATURE_CONFIG_PATH):
                with open(settings.FEATURE_CONFIG_PATH, 'r') as f:
                    self.feature_config = json.load(f)
                self.feature_names = self.feature_config.get("feature_names", [])
                self.optimal_threshold = self.feature_config.get("threshold", 0.5)
                logger.info(f"Loaded feature config with {len(self.feature_names)} features, threshold: {self.optimal_threshold}")

            if self.model is not None and self.feature_names:
                self.explainer = FraudExplainer(self.model, self.feature_names)
                self.explanation_service = ExplanationService(self.explainer)
                logger.info("Initialized FraudExplainer and ExplanationService.")
        except Exception as exc:
            logger.error(f"Failed loading ML artifacts: {exc}")

    def prepare_feature_row(self, raw_input: Dict[str, Any]) -> pd.DataFrame:
        """
        Transforms raw transaction attributes into the exact feature vector expected by the model.
        """
        df = pd.DataFrame([raw_input])
        
        # Payment method one-hot encoding
        payment_methods = ['Credit Card', 'Debit Card', 'Net Banking', 'UPI', 'Wallet']
        current_method = raw_input.get('payment_method', 'UPI')
        for pm in payment_methods:
            df[f'pay_{pm}'] = 1 if pm == current_method else 0
            
        # Ensure base columns exist
        if 'transaction_hour' not in df.columns or df['transaction_hour'].iloc[0] is None:
            df['transaction_hour'] = 12
        if 'transaction_day' not in df.columns or df['transaction_day'].iloc[0] is None:
            df['transaction_day'] = 2
            
        # Defaults for missing telemetry
        defaults = {
            'device_age_days': 30,
            'failed_attempts': 0,
            'transactions_last_5min': 0,
            'transactions_last_10min': 0,
            'transactions_last_1hr': 0,
            'amount_last_1hr': 0.0,
            'is_new_device': False,
            'is_new_location': False,
            'device_transaction_count': 10,
            'location_change': 0,
            'distance_from_previous': 0.0,
            'historical_frequency': 1.0,
            'avg_transaction_amount': 5000.0,
            'amount_deviation': 1.0
        }
        for k, v in defaults.items():
            if k not in df.columns or df[k].iloc[0] is None:
                df[k] = v
                
        # Derive amount_deviation if not explicitly given
        if 'amount_deviation' not in raw_input or raw_input.get('amount_deviation') is None:
            if df['avg_transaction_amount'].iloc[0] > 0:
                df['amount_deviation'] = df['transaction_amount'].iloc[0] / df['avg_transaction_amount'].iloc[0]

        # Apply feature engineering modules
        df = engineer_transaction_features(df)
        df = engineer_velocity_features(df)
        df = engineer_behavioural_features(df)

        # Align columns with trained feature set
        feature_df = pd.DataFrame(0.0, index=[0], columns=self.feature_names)
        for col in self.feature_names:
            if col in df.columns:
                feature_df[col] = df[col].iloc[0]

        # Apply standard scaling if available
        if self.scaler is not None:
            cols_to_scale = [c for c in self.feature_names if not c.startswith('pay_')]
            feature_df[cols_to_scale] = self.scaler.transform(feature_df[cols_to_scale])

        return feature_df

    def assess_transaction(self, raw_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        End-to-end evaluation: feature preparation -> model prediction -> SHAP explanation -> recommendation.
        """
        feature_df = self.prepare_feature_row(raw_input)
        
        # 1. Prediction
        if self.model is not None:
            proba = float(self.model.predict_proba(feature_df)[0, 1])
        else:
            # Fallback heuristic probability if model not loaded
            proba = 0.05
            if raw_input.get('is_new_device') and raw_input.get('failed_attempts', 0) > 2:
                proba = 0.85
                
        # 2. Risk Scoring & Banding
        risk_score = probability_to_risk_score(proba, k=10.0, threshold=self.optimal_threshold)
        risk_level_enum = get_risk_level(risk_score)
        risk_level = risk_level_enum.value
        
        # 3. SHAP Explainability
        explanation = {}
        if self.explanation_service:
            explanation = self.explanation_service.get_explanation(raw_input, feature_df)
            
        risk_factors = explanation.get("risk_factors", [])
        
        # 4. Action Recommendation
        recommendation = generate_recommendation(risk_level, risk_factors)
        
        return {
            "fraud_probability": round(proba, 4),
            "risk_score": int(risk_score),
            "risk_level": risk_level,
            "recommended_action": recommendation,
            "risk_factors": risk_factors,
            "base_risk_score": explanation.get("base_risk_score", 10.0),
            "total_risk_adjustment": explanation.get("total_risk_adjustment", 0.0)
        }

# Global singleton instance
risk_engine = RiskEngine()
