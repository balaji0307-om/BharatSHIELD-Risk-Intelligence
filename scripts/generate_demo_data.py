"""
BharatSHIELD — Realistic Synthetic Transaction Data Generator (v2)

Generates Indian-context payment transaction data with OVERLAPPING distributions
between legitimate and fraudulent transactions, making the classification problem
genuinely challenging (no trivially separable features).

Key design principles:
- Feature distributions OVERLAP between fraud and legit (30-40% shared range)
- 35% of fraud is "subtle" (only 1-2 red flags)
- 5% of legit has "suspicious-looking" patterns (false positive pressure)
- Fraud ring entities share device_ids/IPs for graph detection
- Realistic Indian payment ecosystem context (UPI-heavy, INR amounts, IST hours)

Usage:
    python scripts/generate_demo_data.py
    python scripts/generate_demo_data.py --num-transactions 20000 --fraud-rate 0.04
"""

import argparse
import uuid
import datetime
import random
import os
import hashlib
from pathlib import Path
from typing import List, Dict, Any

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MERCHANTS = [
    'MER_razorpay_001', 'MER_razorpay_002', 'MER_razorpay_003',
    'MER_phonepe_001', 'MER_phonepe_002', 'MER_phonepe_003',
    'MER_paytm_001', 'MER_paytm_002',
    'MER_bharatpe_001', 'MER_pine_001',
]

PAYMENT_METHODS = ['UPI', 'Credit Card', 'Debit Card', 'Net Banking', 'Wallet']
PAYMENT_PROBS = [0.45, 0.25, 0.15, 0.08, 0.07]

INDIAN_CITIES = [
    'Mumbai', 'Delhi', 'Bangalore', 'Chennai', 'Hyderabad',
    'Pune', 'Kolkata', 'Jaipur', 'Ahmedabad', 'Lucknow',
    'Kochi', 'Chandigarh', 'Indore', 'Nagpur', 'Bhopal',
    'Surat', 'Coimbatore', 'Visakhapatnam', 'Patna', 'Guwahati',
]

# Realistic IST hour distribution for legitimate transactions (business-hours heavy)
LEGIT_HOUR_PROBS = np.array([
    0.012, 0.008, 0.005, 0.004, 0.004, 0.008,   # 0-5 AM
    0.018, 0.035, 0.055, 0.070, 0.080, 0.082,     # 6-11 AM
    0.078, 0.075, 0.070, 0.065, 0.068, 0.075,     # 12-5 PM
    0.078, 0.072, 0.055, 0.038, 0.028, 0.018,     # 6-11 PM
])
LEGIT_HOUR_PROBS = LEGIT_HOUR_PROBS / LEGIT_HOUR_PROBS.sum()

# Fraud skews toward night but still has daytime presence (40%)
FRAUD_HOUR_PROBS = np.array([
    0.09, 0.11, 0.12, 0.10, 0.08, 0.05,          # 0-5 AM (heavier)
    0.025, 0.025, 0.030, 0.030, 0.030, 0.030,     # 6-11 AM (present but lower)
    0.030, 0.030, 0.025, 0.025, 0.025, 0.030,     # 12-5 PM
    0.035, 0.035, 0.035, 0.035, 0.045, 0.065,     # 6-11 PM (rising toward night)
])
FRAUD_HOUR_PROBS = FRAUD_HOUR_PROBS / FRAUD_HOUR_PROBS.sum()


def _generate_device_ids(n_unique: int, seed: int = 42) -> List[str]:
    """Generate a pool of device IDs for reuse."""
    rng = random.Random(seed)
    return [f"DEV-{rng.randint(100, 999)}-{uuid.UUID(int=rng.getrandbits(128)).hex[:6]}" for _ in range(n_unique)]


def _generate_user_ids(n_unique: int, seed: int = 42) -> List[str]:
    """Generate a pool of user IDs."""
    rng = random.Random(seed + 100)
    return [f"USR-{rng.randint(10000, 99999)}" for _ in range(n_unique)]


def _generate_ip_addresses(n: int, rng: np.random.RandomState) -> List[str]:
    """Generate realistic Indian IP addresses (major ISP ranges)."""
    prefixes = ['49.36', '59.89', '103.15', '106.51', '117.194',
                '122.161', '157.35', '182.64', '223.176', '14.139']
    ips = []
    for _ in range(n):
        prefix = rng.choice(prefixes)
        octet3 = rng.randint(0, 255)
        octet4 = rng.randint(1, 254)
        ips.append(f"{prefix}.{octet3}.{octet4}")
    return ips


# ---------------------------------------------------------------------------
# Core Generator
# ---------------------------------------------------------------------------

def generate_transactions(
    num_transactions: int = 15000,
    fraud_rate: float = 0.035,
    seed: int = 42,
) -> pd.DataFrame:
    """
    Generate synthetic transaction data with overlapping distributions.

    Key overlaps injected:
    - 40% of fraud uses amounts from the legit distribution
    - 30% of fraud has normal velocity (0-2 txn in 5min)
    - 25% of fraud has 0-1 failed attempts
    - 20% of fraud has low distance (0-50km)
    - 5% of legit has suspicious patterns (high velocity, new device, etc.)
    - 35% of fraud is "subtle" with only 1-2 anomalous features

    Fraud ring injection:
    - 5-8 shared device_ids used across 3-6 fraud transactions each
    - Creates entity graph relationships for network detection
    """
    rng = np.random.RandomState(seed)
    py_rng = random.Random(seed)

    num_fraud = int(num_transactions * fraud_rate)
    num_legit = num_transactions - num_fraud

    # --- Device / User pools ---
    device_pool = _generate_device_ids(200, seed)
    user_pool = _generate_user_ids(150, seed)

    # Fraud ring device IDs (shared across multiple fraud transactions)
    fraud_ring_devices = _generate_device_ids(7, seed + 999)
    fraud_ring_ips = [f"103.15.{rng.randint(1, 50)}.{rng.randint(1, 254)}" for _ in range(4)]

    # ===================================================================
    # LEGITIMATE TRANSACTIONS
    # ===================================================================
    legit_amounts = np.clip(
        rng.lognormal(mean=7.8, sigma=1.3, size=num_legit), 50, 120000
    )

    legit_device_ages = np.clip(
        rng.gamma(shape=3.0, scale=120, size=num_legit).astype(int), 1, 1200
    )

    # Most legit: 0 failed attempts, but ~8% have 2-3 (overlap with fraud)
    legit_failed = rng.choice(
        [0, 1, 2, 3], size=num_legit,
        p=[0.78, 0.14, 0.06, 0.02]
    )

    # Velocity: mostly low, but 5% have moderate bursts (overlap with fraud)
    legit_v5 = rng.choice(
        [0, 1, 2, 3, 4, 5], size=num_legit,
        p=[0.60, 0.22, 0.10, 0.04, 0.025, 0.015]
    )
    legit_v10 = np.clip(legit_v5 + rng.choice([0, 1, 2, 3], size=num_legit, p=[0.5, 0.3, 0.15, 0.05]), 0, 15)
    legit_v1hr = np.clip(rng.poisson(lam=3.5, size=num_legit), 0, 25)

    # New device: 15% (intentionally higher than before to create overlap)
    legit_new_device = rng.choice([True, False], size=num_legit, p=[0.15, 0.85])
    legit_new_location = rng.choice([True, False], size=num_legit, p=[0.12, 0.88])

    legit_device_txn_count = np.clip(
        rng.lognormal(mean=4.0, sigma=1.5, size=num_legit).astype(int), 1, 600
    )

    legit_loc_change = rng.choice([0, 1, 2, 3, 4], size=num_legit, p=[0.65, 0.22, 0.08, 0.035, 0.015])

    # Distance: mostly small, but 5% have 100-500km (business travelers)
    legit_distance = np.where(
        rng.rand(num_legit) < 0.05,
        rng.uniform(100, 500, num_legit),
        np.clip(rng.exponential(scale=20, size=num_legit), 0, 80)
    )

    legit_avg_amount = legit_amounts * rng.uniform(0.6, 1.5, num_legit)
    legit_amount_dev = legit_amounts / np.maximum(legit_avg_amount, 1)
    legit_amount_1hr = legit_v1hr * (legit_avg_amount * rng.uniform(0.7, 1.3, num_legit))
    legit_hist_freq = np.clip(rng.lognormal(mean=0.5, sigma=0.8, size=num_legit), 0.1, 8.0)

    # Assign devices and users
    legit_device_ids = rng.choice(device_pool, size=num_legit)
    legit_user_ids = rng.choice(user_pool, size=num_legit)
    legit_locations = rng.choice(INDIAN_CITIES, size=num_legit)
    legit_ips = _generate_ip_addresses(num_legit, rng)

    legit_data = pd.DataFrame({
        'transaction_id': [str(uuid.UUID(int=py_rng.getrandbits(128))) for _ in range(num_legit)],
        'merchant_id': rng.choice(MERCHANTS, num_legit),
        'user_id': legit_user_ids,
        'device_id': legit_device_ids,
        'ip_address': legit_ips,
        'transaction_amount': np.round(legit_amounts, 2),
        'transaction_hour': rng.choice(range(24), p=LEGIT_HOUR_PROBS, size=num_legit),
        'transaction_day': rng.randint(0, 7, size=num_legit),
        'payment_method': rng.choice(PAYMENT_METHODS, p=PAYMENT_PROBS, size=num_legit),
        'device_age_days': legit_device_ages,
        'failed_attempts': legit_failed,
        'transactions_last_5min': legit_v5,
        'transactions_last_10min': legit_v10,
        'transactions_last_1hr': legit_v1hr,
        'amount_last_1hr': np.round(legit_amount_1hr, 2),
        'is_new_device': legit_new_device,
        'is_new_location': legit_new_location,
        'device_transaction_count': legit_device_txn_count,
        'avg_transaction_amount': np.round(legit_avg_amount, 2),
        'amount_deviation': np.round(legit_amount_dev, 4),
        'historical_frequency': np.round(legit_hist_freq, 2),
        'location_change': legit_loc_change,
        'distance_from_previous': np.round(legit_distance, 1),
        'location': legit_locations,
        'is_fraud': 0,
    })

    # --- Inject 5% "suspicious-looking" legit (false positive pressure) ---
    n_suspicious_legit = int(num_legit * 0.05)
    sus_idx = rng.choice(num_legit, size=n_suspicious_legit, replace=False)
    legit_data.loc[sus_idx, 'is_new_device'] = True
    legit_data.loc[sus_idx, 'transactions_last_5min'] = rng.randint(3, 7, size=n_suspicious_legit)
    legit_data.loc[sus_idx, 'failed_attempts'] = rng.choice([2, 3, 4], size=n_suspicious_legit)
    legit_data.loc[sus_idx, 'distance_from_previous'] = rng.uniform(150, 800, size=n_suspicious_legit).round(1)

    # ===================================================================
    # FRAUDULENT TRANSACTIONS
    # ===================================================================

    # Amount: 40% drawn from LEGIT distribution (overlap), 60% from fraud-heavy
    fraud_amount_from_legit = rng.lognormal(mean=7.8, sigma=1.3, size=num_fraud)
    fraud_amount_heavy = rng.lognormal(mean=9.2, sigma=1.1, size=num_fraud)
    fraud_amount_mask = rng.rand(num_fraud) < 0.40
    fraud_amounts = np.where(fraud_amount_mask, fraud_amount_from_legit, fraud_amount_heavy)
    fraud_amounts = np.clip(fraud_amounts, 100, 400000)

    # Hours: 40% from legit distribution, 60% night-heavy
    fraud_hours_from_legit = rng.choice(range(24), p=LEGIT_HOUR_PROBS, size=num_fraud)
    fraud_hours_night = rng.choice(range(24), p=FRAUD_HOUR_PROBS, size=num_fraud)
    fraud_hour_mask = rng.rand(num_fraud) < 0.40
    fraud_hours = np.where(fraud_hour_mask, fraud_hours_from_legit, fraud_hours_night)

    # Device age: mostly new, but 30% have normal device age
    fraud_device_age_new = rng.randint(0, 15, size=num_fraud)
    fraud_device_age_normal = rng.gamma(shape=2.5, scale=100, size=num_fraud).astype(int)
    fraud_device_mask = rng.rand(num_fraud) < 0.30
    fraud_device_ages = np.clip(
        np.where(fraud_device_mask, fraud_device_age_normal, fraud_device_age_new),
        0, 500
    )

    # Failed attempts: 25% have 0-1 (overlap with legit)
    fraud_failed_low = rng.choice([0, 1], size=num_fraud, p=[0.6, 0.4])
    fraud_failed_high = rng.choice([2, 3, 4, 5, 6, 7], size=num_fraud, p=[0.20, 0.25, 0.25, 0.15, 0.10, 0.05])
    fraud_failed_mask = rng.rand(num_fraud) < 0.25
    fraud_failed = np.where(fraud_failed_mask, fraud_failed_low, fraud_failed_high)

    # Velocity: 30% have normal velocity (overlap)
    fraud_v5_high = rng.choice([2, 4, 6, 8, 10, 13], size=num_fraud, p=[0.10, 0.20, 0.25, 0.22, 0.15, 0.08])
    fraud_v5_normal = rng.choice([0, 1, 2], size=num_fraud, p=[0.50, 0.35, 0.15])
    fraud_v5_mask = rng.rand(num_fraud) < 0.30
    fraud_v5 = np.where(fraud_v5_mask, fraud_v5_normal, fraud_v5_high)

    fraud_v10 = np.clip(fraud_v5 + rng.choice([1, 2, 3, 5, 7], size=num_fraud, p=[0.15, 0.25, 0.30, 0.20, 0.10]), 0, 25)
    fraud_v1hr = np.clip(rng.randint(3, 40, size=num_fraud), 0, 50)

    # New device/location: fraud-heavy but with overlap
    fraud_new_device = rng.choice([True, False], size=num_fraud, p=[0.65, 0.35])
    fraud_new_location = rng.choice([True, False], size=num_fraud, p=[0.60, 0.40])

    fraud_device_txn_count = np.clip(
        rng.choice(
            [0, 1, 2, 3, 5, 10, 20, 50],
            size=num_fraud,
            p=[0.15, 0.20, 0.20, 0.15, 0.10, 0.08, 0.07, 0.05]
        ), 0, 100
    )

    fraud_loc_change = rng.choice([0, 1, 2, 3, 4, 5], size=num_fraud, p=[0.10, 0.20, 0.25, 0.22, 0.15, 0.08])

    # Distance: 20% have small distance (overlap with legit)
    fraud_dist_far = np.clip(rng.exponential(scale=400, size=num_fraud), 50, 4000)
    fraud_dist_near = rng.uniform(0, 50, num_fraud)
    fraud_dist_mask = rng.rand(num_fraud) < 0.20
    fraud_distance = np.where(fraud_dist_mask, fraud_dist_near, fraud_dist_far)

    fraud_avg_amount = fraud_amounts * rng.uniform(0.15, 0.7, num_fraud)
    fraud_amount_dev = fraud_amounts / np.maximum(fraud_avg_amount, 1)
    fraud_amount_1hr = fraud_v1hr * fraud_amounts * rng.uniform(0.5, 1.2, num_fraud)
    fraud_hist_freq = np.clip(rng.uniform(1.0, 18.0, num_fraud), 0.1, 25.0)

    # Assign devices and users (with fraud ring devices)
    fraud_device_ids = list(rng.choice(device_pool, size=num_fraud))
    fraud_user_ids = list(rng.choice(user_pool, size=num_fraud))
    fraud_locations = list(rng.choice(INDIAN_CITIES, size=num_fraud))
    fraud_ips = _generate_ip_addresses(num_fraud, rng)

    # --- Inject fraud rings: shared device IDs across clusters ---
    ring_txn_indices = []
    ring_idx = 0
    for ring_dev in fraud_ring_devices:
        cluster_size = py_rng.randint(3, 6)
        indices = rng.choice(num_fraud, size=min(cluster_size, num_fraud), replace=False).tolist()
        ring_ip = py_rng.choice(fraud_ring_ips)
        ring_cities = py_rng.sample(INDIAN_CITIES, min(3, len(INDIAN_CITIES)))
        for i, idx in enumerate(indices):
            fraud_device_ids[idx] = ring_dev
            fraud_ips[idx] = ring_ip
            fraud_locations[idx] = ring_cities[i % len(ring_cities)]
            ring_txn_indices.append(idx)
        ring_idx += 1

    fraud_data = pd.DataFrame({
        'transaction_id': [str(uuid.UUID(int=py_rng.getrandbits(128))) for _ in range(num_fraud)],
        'merchant_id': rng.choice(MERCHANTS, num_fraud),
        'user_id': fraud_user_ids,
        'device_id': fraud_device_ids,
        'ip_address': fraud_ips,
        'transaction_amount': np.round(fraud_amounts, 2),
        'transaction_hour': fraud_hours.astype(int),
        'transaction_day': rng.randint(0, 7, size=num_fraud),
        'payment_method': rng.choice(PAYMENT_METHODS, size=num_fraud),
        'device_age_days': fraud_device_ages.astype(int),
        'failed_attempts': fraud_failed.astype(int),
        'transactions_last_5min': fraud_v5.astype(int),
        'transactions_last_10min': fraud_v10.astype(int),
        'transactions_last_1hr': fraud_v1hr.astype(int),
        'amount_last_1hr': np.round(fraud_amount_1hr, 2),
        'is_new_device': fraud_new_device,
        'is_new_location': fraud_new_location,
        'device_transaction_count': fraud_device_txn_count.astype(int),
        'avg_transaction_amount': np.round(fraud_avg_amount, 2),
        'amount_deviation': np.round(fraud_amount_dev, 4),
        'historical_frequency': np.round(fraud_hist_freq, 2),
        'location_change': fraud_loc_change.astype(int),
        'distance_from_previous': np.round(fraud_distance, 1),
        'location': fraud_locations,
        'is_fraud': 1,
    })

    # --- Make 50% of fraud "subtle" (only 1-2 anomalous features) ---
    # This is critical for preventing perfect model separation
    n_subtle = int(num_fraud * 0.50)
    subtle_idx = rng.choice(num_fraud, size=n_subtle, replace=False)
    
    # Reset ALL features to legit-like values first
    fraud_data.loc[subtle_idx, 'transaction_amount'] = np.clip(
        rng.lognormal(mean=7.8, sigma=1.3, size=n_subtle), 200, 30000
    ).round(2)
    fraud_data.loc[subtle_idx, 'transaction_hour'] = rng.choice(range(24), p=LEGIT_HOUR_PROBS, size=n_subtle)
    fraud_data.loc[subtle_idx, 'failed_attempts'] = rng.choice([0, 1], size=n_subtle, p=[0.80, 0.20])
    fraud_data.loc[subtle_idx, 'transactions_last_5min'] = rng.choice([0, 1, 2], size=n_subtle, p=[0.55, 0.30, 0.15])
    fraud_data.loc[subtle_idx, 'transactions_last_10min'] = rng.choice([0, 1, 2, 3], size=n_subtle, p=[0.4, 0.3, 0.2, 0.1])
    fraud_data.loc[subtle_idx, 'transactions_last_1hr'] = np.clip(rng.poisson(lam=3, size=n_subtle), 0, 15)
    fraud_data.loc[subtle_idx, 'distance_from_previous'] = np.clip(rng.exponential(scale=20, size=n_subtle), 0, 80).round(1)
    fraud_data.loc[subtle_idx, 'device_age_days'] = rng.randint(15, 500, size=n_subtle)
    fraud_data.loc[subtle_idx, 'is_new_device'] = rng.choice([True, False], size=n_subtle, p=[0.15, 0.85])
    fraud_data.loc[subtle_idx, 'is_new_location'] = rng.choice([True, False], size=n_subtle, p=[0.12, 0.88])
    fraud_data.loc[subtle_idx, 'device_transaction_count'] = np.clip(rng.lognormal(mean=3.5, sigma=1.5, size=n_subtle).astype(int), 1, 300)
    fraud_data.loc[subtle_idx, 'location_change'] = rng.choice([0, 1, 2], size=n_subtle, p=[0.65, 0.25, 0.10])
    fraud_data.loc[subtle_idx, 'historical_frequency'] = np.clip(rng.lognormal(mean=0.5, sigma=0.8, size=n_subtle), 0.1, 8.0).round(2)
    
    # Now inject exactly 1-2 anomalous signals per subtle fraud
    for idx in subtle_idx:
        n_signals = rng.choice([1, 2])
        signals = rng.choice(['velocity', 'location', 'device', 'amount', 'failed'], size=n_signals, replace=False)
        for signal in signals:
            if signal == 'velocity':
                fraud_data.loc[idx, 'transactions_last_5min'] = rng.randint(4, 9)
            elif signal == 'location':
                fraud_data.loc[idx, 'distance_from_previous'] = round(rng.uniform(150, 1200), 1)
                fraud_data.loc[idx, 'is_new_location'] = True
            elif signal == 'device':
                fraud_data.loc[idx, 'is_new_device'] = True
                fraud_data.loc[idx, 'device_age_days'] = rng.randint(0, 3)
                fraud_data.loc[idx, 'device_transaction_count'] = rng.randint(0, 2)
            elif signal == 'amount':
                fraud_data.loc[idx, 'transaction_amount'] = round(rng.lognormal(9.5, 0.8), 2)
            elif signal == 'failed':
                fraud_data.loc[idx, 'failed_attempts'] = rng.randint(3, 7)
    
    # --- Add random noise to ALL fraud rows (jitter features) ---
    for i in range(num_fraud):
        if rng.rand() < 0.15:  # 15% get some random legit-like feature values
            feat = rng.choice(['device_age_days', 'device_transaction_count', 'historical_frequency'])
            if feat == 'device_age_days':
                fraud_data.loc[i, feat] = rng.randint(50, 500)
            elif feat == 'device_transaction_count':
                fraud_data.loc[i, feat] = rng.randint(10, 200)
            elif feat == 'historical_frequency':
                fraud_data.loc[i, feat] = round(rng.uniform(0.5, 4.0), 2)

    # ===================================================================
    # COMBINE & FINALIZE
    # ===================================================================
    df = pd.concat([legit_data, fraud_data], ignore_index=True)
    df = df.sample(frac=1, random_state=seed).reset_index(drop=True)

    # Add timestamps (spanning last 30 days, sorted)
    end_date = datetime.datetime.now()
    start_date = end_date - datetime.timedelta(days=30)
    total_seconds = int((end_date - start_date).total_seconds())
    timestamps = sorted([
        start_date + datetime.timedelta(seconds=py_rng.randint(0, total_seconds))
        for _ in range(len(df))
    ])
    df['timestamp'] = timestamps

    # Recalculate derived fields for consistency
    df['amount_deviation'] = (df['transaction_amount'] / df['avg_transaction_amount'].clip(lower=1)).round(4)
    df['amount_last_1hr'] = (df['transactions_last_1hr'] * df['avg_transaction_amount'] * rng.uniform(0.7, 1.3, len(df))).round(2)

    return df


def create_demo_subset(df: pd.DataFrame, seed: int = 42) -> pd.DataFrame:
    """
    Create a curated 200-transaction demo subset with showcase transactions.

    Includes:
    - 5-10 carefully designed showcase transactions (LOW through CRITICAL)
    - A fraud ring cluster (4 transactions sharing a device)
    - A mix of risk levels for realistic dashboard display
    """
    rng = np.random.RandomState(seed)

    # Select a representative sample
    fraud_df = df[df['is_fraud'] == 1]
    legit_df = df[df['is_fraud'] == 0]

    # Pick legit samples with variety
    demo_legit = legit_df.sample(n=min(170, len(legit_df)), random_state=seed)

    # Pick fraud samples ensuring we get fraud ring members
    fraud_ring_mask = fraud_df['device_id'].str.startswith('DEV-') & fraud_df.duplicated(subset='device_id', keep=False)
    ring_fraud = fraud_df[fraud_ring_mask].head(8)
    other_fraud = fraud_df[~fraud_df.index.isin(ring_fraud.index)].sample(
        n=min(22, len(fraud_df) - len(ring_fraud)), random_state=seed
    )

    demo_df = pd.concat([demo_legit, ring_fraud, other_fraud], ignore_index=True)
    demo_df = demo_df.sample(frac=1, random_state=seed).reset_index(drop=True)

    return demo_df


def print_data_summary(df: pd.DataFrame) -> None:
    """Print comprehensive data statistics."""
    fraud = df[df['is_fraud'] == 1]
    legit = df[df['is_fraud'] == 0]

    print("\n" + "=" * 60)
    print("  BharatSHIELD — Synthetic Data Summary (v2)")
    print("=" * 60)

    print(f"\n  Total Transactions:     {len(df):,}")
    print(f"  Legitimate:             {len(legit):,} ({len(legit)/len(df)*100:.1f}%)")
    print(f"  Fraudulent:             {len(fraud):,} ({len(fraud)/len(df)*100:.1f}%)")

    print(f"\n  --- Amount Distribution (INR) ---")
    print(f"  {'':20s} {'Legit':>12s}  {'Fraud':>12s}")
    print(f"  {'Mean':20s} {legit['transaction_amount'].mean():>12,.0f}  {fraud['transaction_amount'].mean():>12,.0f}")
    print(f"  {'Median':20s} {legit['transaction_amount'].median():>12,.0f}  {fraud['transaction_amount'].median():>12,.0f}")
    print(f"  {'Std':20s} {legit['transaction_amount'].std():>12,.0f}  {fraud['transaction_amount'].std():>12,.0f}")

    print(f"\n  --- Feature Overlap Analysis ---")
    for col in ['failed_attempts', 'transactions_last_5min', 'device_age_days', 'distance_from_previous']:
        l_range = (legit[col].min(), legit[col].max())
        f_range = (fraud[col].min(), fraud[col].max())
        overlap_min = max(l_range[0], f_range[0])
        overlap_max = min(l_range[1], f_range[1])
        if overlap_max >= overlap_min:
            overlap_pct = (overlap_max - overlap_min) / max(l_range[1] - l_range[0], 1) * 100
            print(f"  {col:30s}  overlap: {overlap_pct:.0f}%")

    print(f"\n  --- New Device Rates ---")
    print(f"  Legit new_device rate:  {legit['is_new_device'].mean():.1%}")
    print(f"  Fraud new_device rate:  {fraud['is_new_device'].mean():.1%}")

    # Fraud ring stats
    fraud_devices = fraud.groupby('device_id').size()
    ring_devices = fraud_devices[fraud_devices >= 3]
    print(f"\n  --- Fraud Ring Stats ---")
    print(f"  Devices with 3+ fraud txns:  {len(ring_devices)}")
    print(f"  Total ring transactions:     {ring_devices.sum()}")

    print(f"\n  Unique merchants:       {df['merchant_id'].nunique()}")
    print(f"  Unique devices:         {df['device_id'].nunique()}")
    print(f"  Unique users:           {df['user_id'].nunique()}")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="Generate realistic synthetic transaction data for BharatSHIELD.")
    parser.add_argument('--num-transactions', type=int, default=15000, help='Total transactions to generate')
    parser.add_argument('--fraud-rate', type=float, default=0.035, help='Fraud ratio (default: 3.5%%)')
    parser.add_argument('--output-dir', type=str, default='data/raw', help='Output directory for CSVs')
    parser.add_argument('--seed', type=int, default=42, help='Random seed for reproducibility')
    args = parser.parse_args()

    print(f"Generating {args.num_transactions:,} transactions with ~{args.fraud_rate*100:.1f}% fraud rate...")
    df = generate_transactions(
        num_transactions=args.num_transactions,
        fraud_rate=args.fraud_rate,
        seed=args.seed,
    )

    base_path = Path(__file__).parent.parent
    out_dir = base_path / args.output_dir if not Path(args.output_dir).is_absolute() else Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Save full dataset
    full_path = out_dir / 'transactions.csv'
    df.to_csv(full_path, index=False)
    print(f"Saved full dataset -> {full_path}")

    # Save curated demo subset
    demo_df = create_demo_subset(df, seed=args.seed)
    demo_path = out_dir / 'demo_transactions.csv'
    demo_df.to_csv(demo_path, index=False)
    print(f"Saved demo dataset -> {demo_path} ({len(demo_df)} transactions)")

    print_data_summary(df)


if __name__ == '__main__':
    main()
