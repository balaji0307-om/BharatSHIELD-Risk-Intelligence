from sklearn.model_selection import train_test_split
import pandas as pd
from typing import Tuple, List

def split_dataset(df: pd.DataFrame, feature_cols: List[str], target_col: str, 
                  test_size: float = 0.15, val_size: float = 0.15, random_state: int = 42) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.Series, pd.Series, pd.Series]:
    """
    Splits the dataset into train, validation, and test sets with stratification.
    
    Args:
        df (pd.DataFrame): The full dataset.
        feature_cols (List[str]): List of feature column names present in the dataframe (can be post-encoding).
        target_col (str): The target column name.
        test_size (float): Proportion of the dataset to include in the test split.
        val_size (float): Proportion of the dataset to include in the validation split.
        random_state (int): Random seed.
        
    Returns:
        Tuple containing X_train, X_val, X_test, y_train, y_val, y_test
    """
    
    # Available feature columns after potential encoding
    available_features = [col for col in df.columns if col != target_col and col not in ['transaction_id', 'merchant_id', 'timestamp']]
    
    X = df[available_features]
    y = df[target_col]
    
    # First split to separate out the test set
    X_temp, X_test, y_temp, y_test = train_test_split(
        X, y, test_size=test_size, stratify=y, random_state=random_state
    )
    
    # Calculate proportion of remaining data to allocate to validation set
    val_ratio = val_size / (1.0 - test_size)
    
    # Second split to separate train and validation sets
    X_train, X_val, y_train, y_val = train_test_split(
        X_temp, y_temp, test_size=val_ratio, stratify=y_temp, random_state=random_state
    )
    
    return X_train, X_val, X_test, y_train, y_val, y_test
