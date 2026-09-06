import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from typing import Tuple, Optional, List

def preprocess_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Handles missing values and caps outliers in the dataset.
    
    Args:
        df (pd.DataFrame): The input dataframe.
        
    Returns:
        pd.DataFrame: Cleaned dataframe.
    """
    df_clean = df.copy()
    
    numeric_cols = df_clean.select_dtypes(include=[np.number]).columns
    categorical_cols = df_clean.select_dtypes(include=['object', 'category']).columns
    
    # Handle missing values
    for col in numeric_cols:
        if df_clean[col].isnull().any():
            df_clean[col] = df_clean[col].fillna(df_clean[col].median())
            
    for col in categorical_cols:
        if df_clean[col].isnull().any():
            df_clean[col] = df_clean[col].fillna(df_clean[col].mode()[0])
            
    # Cap outliers using IQR method for specific continuous variables
    cols_to_cap = ['transaction_amount', 'distance_from_previous', 'amount_last_1hr']
    for col in cols_to_cap:
        if col in df_clean.columns:
            Q1 = df_clean[col].quantile(0.25)
            Q3 = df_clean[col].quantile(0.75)
            IQR = Q3 - Q1
            upper_bound = Q3 + 1.5 * IQR
            df_clean[col] = np.where(df_clean[col] > upper_bound, upper_bound, df_clean[col])
            
    return df_clean

def encode_categoricals(df: pd.DataFrame) -> pd.DataFrame:
    """
    One-hot encodes categorical variables and label encodes booleans.
    
    Args:
        df (pd.DataFrame): The input dataframe.
        
    Returns:
        pd.DataFrame: Encoded dataframe.
    """
    df_encoded = df.copy()
    
    # One-hot encode payment_method
    if 'payment_method' in df_encoded.columns:
        df_encoded = pd.get_dummies(df_encoded, columns=['payment_method'], prefix='pay')
        
    # Boolean to int mapping
    bool_cols = ['is_new_device', 'is_new_location']
    for col in bool_cols:
        if col in df_encoded.columns:
            df_encoded[col] = df_encoded[col].astype(int)
            
    return df_encoded

def scale_features(df: pd.DataFrame, feature_cols: List[str], scaler: Optional[StandardScaler] = None) -> Tuple[pd.DataFrame, StandardScaler]:
    """
    Scales numerical features using StandardScaler.
    
    Args:
        df (pd.DataFrame): The input dataframe.
        feature_cols (List[str]): Columns to scale. Note: some feature_cols might be categorical after OHE. 
                                  Scale only numerical ones.
        scaler (Optional[StandardScaler]): Existing scaler. If None, fits a new one.
        
    Returns:
        Tuple[pd.DataFrame, StandardScaler]: Scaled dataframe and the scaler.
    """
    df_scaled = df.copy()
    
    # Select continuous numerical columns to scale, excluding encoded categoricals and target/ids
    cols_to_scale = [col for col in feature_cols if col in df_scaled.columns and df_scaled[col].dtype in [np.float64, np.float32, np.int64, np.int32] and not col.startswith('pay_')]
    
    if scaler is None:
        scaler = StandardScaler()
        df_scaled[cols_to_scale] = scaler.fit_transform(df_scaled[cols_to_scale])
    else:
        df_scaled[cols_to_scale] = scaler.transform(df_scaled[cols_to_scale])
        
    return df_scaled, scaler
