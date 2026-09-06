"""
Module for extracting behavioural anomaly features.
"""

import pandas as pd
import numpy as np

__all__ = ["engineer_behavioural_features"]

def engineer_behavioural_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Engineer behavioural anomaly risk features.
    Ensures all outputs are strictly numeric.
    """
    if df is None or df.empty:
        return df
        
    df_out = df.copy()
    
    # Amount Z-score
    if 'transaction_amount' in df_out.columns and 'avg_transaction_amount' in df_out.columns and 'amount_deviation' in df_out.columns:
        std = np.maximum(df_out['amount_deviation'], 1.0)
        df_out['amount_zscore'] = ((df_out['transaction_amount'] - df_out['avg_transaction_amount']) / std).astype(float)
        
    # Is unusual amount (0 or 1)
    if 'amount_deviation' in df_out.columns:
        df_out['is_unusual_amount'] = (df_out['amount_deviation'] > 3.0).astype(int)
        
    # Frequency deviation
    if 'current_frequency' in df_out.columns and 'historical_frequency' in df_out.columns:
        df_out['frequency_deviation'] = (df_out['current_frequency'] - df_out['historical_frequency']).astype(float)
        
    # Device risk score (0-1 scale, higher = riskier)
    if all(c in df_out.columns for c in ['is_new_device', 'device_age_days', 'device_transaction_count']):
        new_dev = df_out['is_new_device'].astype(float)
        age_risk = np.exp(-0.1 * df_out['device_age_days'].fillna(0).astype(float))
        tx_risk = np.exp(-0.5 * df_out['device_transaction_count'].fillna(0).astype(float))
        df_out['device_risk_score'] = ((new_dev + age_risk + tx_risk) / 3.0).clip(0.0, 1.0).astype(float)
        
    # Location risk score (0-1 scale, higher = riskier)
    if all(c in df_out.columns for c in ['is_new_location', 'location_change', 'distance_from_previous']):
        new_loc = df_out['is_new_location'].astype(float)
        loc_change = df_out['location_change'].astype(float)
        dist_risk = 1.0 - np.exp(-0.01 * df_out['distance_from_previous'].fillna(0).astype(float))
        df_out['location_risk_score'] = ((new_loc + loc_change + dist_risk) / 3.0).clip(0.0, 1.0).astype(float)
        
    # Combined risk indicators
    risk_flags = ['is_velocity_spike', 'is_unusual_amount', 'is_high_value', 'is_new_device', 'is_new_location']
    available_flags = [c for c in risk_flags if c in df_out.columns]
    if available_flags:
        df_out['combined_risk_indicators'] = df_out[available_flags].fillna(0).astype(int).sum(axis=1).astype(int)
        
    return df_out
