"""
Data splitting with leakage prevention.

Splits by user_id groups so the same user's transactions don't appear in
both train and test sets. Falls back to stratified split if user_id is unavailable.
"""

from sklearn.model_selection import train_test_split, GroupShuffleSplit
import pandas as pd
import numpy as np
from typing import Tuple, List


# Columns that should NEVER be used as model features
NON_FEATURE_COLS = {
    'transaction_id', 'merchant_id', 'timestamp', 'is_fraud',
    'user_id', 'device_id', 'ip_address', 'location',
}


def split_dataset(
    df: pd.DataFrame,
    feature_cols: List[str],
    target_col: str,
    test_size: float = 0.15,
    val_size: float = 0.15,
    random_state: int = 42,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.Series, pd.Series, pd.Series]:
    """
    Splits the dataset into train, validation, and test sets.

    Uses group-based splitting by user_id when available to prevent data leakage
    (same user's transactions appearing in both train and test). Falls back to
    stratified splitting if user_id is not present.

    Args:
        df: The full dataset.
        feature_cols: Feature column names (used for reference; actual features
                      are computed from available columns minus non-feature cols).
        target_col: The target column name.
        test_size: Proportion for test split.
        val_size: Proportion for validation split.
        random_state: Random seed.

    Returns:
        Tuple of (X_train, X_val, X_test, y_train, y_val, y_test)
    """
    # Compute actual feature columns (exclude identifiers, target, metadata)
    available_features = [
        col for col in df.columns
        if col not in NON_FEATURE_COLS
    ]

    X = df[available_features]
    y = df[target_col]

    if 'user_id' in df.columns:
        # --- Group-based split to prevent leakage ---
        groups = df['user_id']

        # Split: test
        gss_test = GroupShuffleSplit(n_splits=1, test_size=test_size, random_state=random_state)
        train_val_idx, test_idx = next(gss_test.split(X, y, groups))

        X_temp, X_test = X.iloc[train_val_idx], X.iloc[test_idx]
        y_temp, y_test = y.iloc[train_val_idx], y.iloc[test_idx]
        groups_temp = groups.iloc[train_val_idx]

        # Split: validation from remaining
        val_ratio = val_size / (1.0 - test_size)
        gss_val = GroupShuffleSplit(n_splits=1, test_size=val_ratio, random_state=random_state)
        train_idx, val_idx = next(gss_val.split(X_temp, y_temp, groups_temp))

        X_train, X_val = X_temp.iloc[train_idx], X_temp.iloc[val_idx]
        y_train, y_val = y_temp.iloc[train_idx], y_temp.iloc[val_idx]
    else:
        # --- Fallback: stratified split ---
        X_temp, X_test, y_temp, y_test = train_test_split(
            X, y, test_size=test_size, stratify=y, random_state=random_state
        )
        val_ratio = val_size / (1.0 - test_size)
        X_train, X_val, y_train, y_val = train_test_split(
            X_temp, y_temp, test_size=val_ratio, stratify=y_temp, random_state=random_state
        )

    return X_train, X_val, X_test, y_train, y_val, y_test
