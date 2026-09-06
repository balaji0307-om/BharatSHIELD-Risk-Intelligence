"""
Module for extracting velocity-based risk features.
"""

import pandas as pd
import numpy as np

__all__ = ["engineer_velocity_features"]

def engineer_velocity_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Engineer velocity-based risk features.
    Ensures all outputs are strictly numeric.
    """
    if df is None or df.empty:
        return df
        
    df_out = df.copy()
    
    # Velocity ratio 5/10
    if 'transactions_last_5min' in df_out.columns and 'transactions_last_10min' in df_out.columns:
        denom = np.maximum(df_out['transactions_last_10min'], 1)
        df_out['velocity_ratio_5_10'] = (df_out['transactions_last_5min'] / denom).astype(float)
        
    # Velocity ratio 10/60
    if 'transactions_last_10min' in df_out.columns and 'transactions_last_1hr' in df_out.columns:
        denom = np.maximum(df_out['transactions_last_1hr'], 1)
        df_out['velocity_ratio_10_60'] = (df_out['transactions_last_10min'] / denom).astype(float)
        
    # Velocity acceleration
    if 'velocity_ratio_5_10' in df_out.columns and 'velocity_ratio_10_60' in df_out.columns:
        df_out['velocity_acceleration'] = (df_out['velocity_ratio_5_10'] - df_out['velocity_ratio_10_60']).astype(float)
        
    # Amount velocity
    if 'amount_last_1hr' in df_out.columns and 'transactions_last_1hr' in df_out.columns:
        denom = np.maximum(df_out['transactions_last_1hr'], 1)
        df_out['amount_velocity'] = (df_out['amount_last_1hr'] / denom).astype(float)
        
    # Is velocity spike (0 or 1)
    if 'transactions_last_5min' in df_out.columns:
        df_out['is_velocity_spike'] = (df_out['transactions_last_5min'] > 3).astype(int)
        
    return df_out
