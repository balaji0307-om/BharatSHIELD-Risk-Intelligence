import pandas as pd
from typing import List, Tuple

def load_dataset(filepath: str) -> pd.DataFrame:
    """
    Loads a dataset from a CSV file, validates required columns, and handles type casting.
    
    Args:
        filepath (str): Path to the CSV file.
        
    Returns:
        pd.DataFrame: Loaded dataset.
    """
    df = pd.read_csv(filepath)
    
    # Essential features to validate (core features only, not entity/metadata columns)
    core_required = get_feature_columns() + [get_target_column()]
    missing_cols = [col for col in core_required if col not in df.columns]
    
    if missing_cols:
        raise ValueError(f"Missing required columns in dataset: {missing_cols}")
        
    # Cast types
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
    bool_cols = ['is_new_device', 'is_new_location']
    for col in bool_cols:
        if col in df.columns:
            df[col] = df[col].astype(bool)
            
    return df

def get_feature_columns() -> List[str]:
    """
    Returns the list of feature column names used for modeling.
    
    Returns:
        List[str]: Feature column names.
    """
    return [
        'transaction_amount',
        'transaction_hour',
        'transaction_day',
        'payment_method',
        'device_age_days',
        'failed_attempts',
        'transactions_last_5min',
        'transactions_last_10min',
        'transactions_last_1hr',
        'amount_last_1hr',
        'is_new_device',
        'is_new_location',
        'device_transaction_count',
        'avg_transaction_amount',
        'amount_deviation',
        'historical_frequency',
        'location_change',
        'distance_from_previous'
    ]

def get_target_column() -> str:
    """
    Returns the name of the target column.
    
    Returns:
        str: Target column name.
    """
    return 'is_fraud'
