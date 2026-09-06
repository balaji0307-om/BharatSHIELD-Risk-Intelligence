"""
Module for extracting transaction-level risk features.
"""

import pandas as pd
import numpy as np

__all__ = ["engineer_transaction_features"]

def engineer_transaction_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Engineer transaction-level risk features from raw transaction data.
    Ensures all outputs are strictly numeric.
    """
    if df is None or df.empty:
        return df
        
    df_out = df.copy()
    
    # Amount bin (numeric ordinal: 0=micro, 1=small, 2=medium, 3=large, 4=very_large)
    if 'transaction_amount' in df_out.columns:
        bins = [-np.inf, 100, 1000, 10000, 50000, np.inf]
        df_out['amount_bin'] = pd.cut(df_out['transaction_amount'], bins=bins, labels=[0, 1, 2, 3, 4], right=False).astype(float)
        df_out['amount_log'] = np.log1p(df_out['transaction_amount'])
        df_out['is_high_value'] = (df_out['transaction_amount'] > 25000).astype(int)

    # Hour bin (numeric ordinal: 0=night, 1=morning, 2=afternoon, 3=evening)
    if 'transaction_hour' in df_out.columns:
        bins = [-np.inf, 6, 12, 18, 23, np.inf]
        # night=0, morning=1, afternoon=2, evening=3, late_night=0
        hour_binned = pd.cut(df_out['transaction_hour'], bins=bins, labels=[0, 1, 2, 3, 0], ordered=False)
        df_out['hour_bin'] = hour_binned.astype(float)

    # Is weekend (0 or 1)
    if 'transaction_day' in df_out.columns:
        df_out['is_weekend'] = df_out['transaction_day'].isin([5, 6, 'Saturday', 'Sunday', 'Sat', 'Sun']).astype(int)

    return df_out
