import argparse
import uuid
import datetime
import random
import os
from pathlib import Path
import numpy as np
import pandas as pd

def generate_transactions(num_transactions=15000, fraud_rate=0.03, seed=42):
    np.random.seed(seed)
    random.seed(seed)
    
    num_fraud = int(num_transactions * fraud_rate)
    num_legit = num_transactions - num_fraud
    
    merchants = [f'MER_razorpay_{str(i).zfill(3)}' for i in range(1, 4)] + \
                [f'MER_phonepe_{str(i).zfill(3)}' for i in range(1, 4)] + \
                [f'MER_paytm_{str(i).zfill(3)}' for i in range(1, 3)] + \
                ['MER_bharatpe_001', 'MER_pine_001']
                
    payment_methods = ['UPI', 'Credit Card', 'Debit Card', 'Net Banking', 'Wallet']
    payment_probs = [0.45, 0.25, 0.20, 0.05, 0.05]
    
    legit_hours_p = np.array([
        0.01, 0.005, 0.005, 0.005, 0.005, 0.01,
        0.02, 0.04, 0.06, 0.07, 0.08, 0.08,
        0.08, 0.08, 0.07, 0.06, 0.07, 0.08,
        0.08, 0.08, 0.06, 0.04, 0.03, 0.02
    ])
    legit_hours_p = legit_hours_p / legit_hours_p.sum()

    fraud_hours_p = np.array([
        0.12, 0.14, 0.15, 0.13, 0.11, 0.06,
        0.02, 0.02, 0.02, 0.02, 0.02, 0.02,
        0.02, 0.02, 0.02, 0.02, 0.02, 0.02,
        0.03, 0.03, 0.03, 0.03, 0.05, 0.06
    ])
    fraud_hours_p = fraud_hours_p / fraud_hours_p.sum()

    # Generate Legitimate Data (with realistic edge cases)
    legit_data = {
        'transaction_id': [str(uuid.uuid4()) for _ in range(num_legit)],
        'merchant_id': np.random.choice(merchants, num_legit),
        'transaction_amount': np.clip(np.random.lognormal(mean=7.6, sigma=1.2, size=num_legit), 50, 65000),
        'transaction_hour': np.random.choice(range(24), p=legit_hours_p, size=num_legit),
        'transaction_day': np.random.randint(0, 7, size=num_legit),
        'payment_method': np.random.choice(payment_methods, p=payment_probs, size=num_legit),
        'device_age_days': np.random.randint(5, 900, size=num_legit),
        'failed_attempts': np.random.choice([0, 1, 2, 3], p=[0.85, 0.10, 0.04, 0.01], size=num_legit),
        'transactions_last_5min': np.random.choice([0, 1, 2, 3, 4], p=[0.70, 0.20, 0.07, 0.02, 0.01], size=num_legit),
        'transactions_last_10min': np.random.choice([0, 1, 2, 3, 5, 7], p=[0.60, 0.22, 0.10, 0.05, 0.02, 0.01], size=num_legit),
        'transactions_last_1hr': np.random.poisson(lam=4, size=num_legit).clip(0, 20),
        'is_new_device': np.random.choice([True, False], p=[0.12, 0.88], size=num_legit),
        'is_new_location': np.random.choice([True, False], p=[0.15, 0.85], size=num_legit),
        'device_transaction_count': np.random.randint(1, 400, size=num_legit),
        'location_change': np.random.choice([0, 1, 2, 3], p=[0.70, 0.22, 0.06, 0.02], size=num_legit),
        'distance_from_previous': np.random.exponential(scale=25, size=num_legit).clip(0, 250),
        'is_fraud': np.zeros(num_legit, dtype=int)
    }
    
    # Historical base features for legit
    legit_data['avg_transaction_amount'] = legit_data['transaction_amount'] * np.random.uniform(0.7, 1.4, num_legit)
    legit_data['amount_deviation'] = legit_data['transaction_amount'] / (legit_data['avg_transaction_amount'] + 1)
    legit_data['amount_last_1hr'] = legit_data['transactions_last_1hr'] * (legit_data['avg_transaction_amount'] * np.random.uniform(0.8, 1.2, num_legit))
    legit_data['historical_frequency'] = np.random.uniform(0.5, 4.5, num_legit)

    # Generate Fraud Data with nuanced patterns
    fraud_data = {
        'transaction_id': [str(uuid.uuid4()) for _ in range(num_fraud)],
        'merchant_id': np.random.choice(merchants, num_fraud),
        'transaction_amount': np.clip(np.random.lognormal(mean=9.5, sigma=1.4, size=num_fraud), 500, 350000),
        'transaction_hour': np.random.choice(range(24), p=fraud_hours_p, size=num_fraud),
        'transaction_day': np.random.randint(0, 7, size=num_fraud),
        'payment_method': np.random.choice(payment_methods, size=num_fraud),
        'device_age_days': np.random.randint(0, 30, size=num_fraud),
        'failed_attempts': np.random.choice([1, 2, 3, 4, 5, 6], p=[0.10, 0.20, 0.30, 0.20, 0.10, 0.10], size=num_fraud),
        'transactions_last_5min': np.random.choice([1, 2, 4, 6, 9, 12], p=[0.10, 0.15, 0.25, 0.25, 0.15, 0.10], size=num_fraud),
        'transactions_last_10min': np.random.choice([2, 4, 7, 11, 16, 20], p=[0.10, 0.15, 0.25, 0.25, 0.15, 0.10], size=num_fraud),
        'transactions_last_1hr': np.random.randint(5, 45, size=num_fraud),
        'is_new_device': np.random.choice([True, False], p=[0.75, 0.25], size=num_fraud),
        'is_new_location': np.random.choice([True, False], p=[0.70, 0.30], size=num_fraud),
        'device_transaction_count': np.random.randint(0, 8, size=num_fraud),
        'location_change': np.random.randint(1, 5, size=num_fraud),
        'distance_from_previous': np.random.exponential(scale=350, size=num_fraud).clip(40, 3000),
        'is_fraud': np.ones(num_fraud, dtype=int)
    }
    
    # Historical base features for fraud
    fraud_data['avg_transaction_amount'] = fraud_data['transaction_amount'] * np.random.uniform(0.2, 0.6, num_fraud)
    fraud_data['amount_deviation'] = fraud_data['transaction_amount'] / (fraud_data['avg_transaction_amount'] + 1)
    fraud_data['amount_last_1hr'] = fraud_data['transactions_last_1hr'] * fraud_data['transaction_amount'] * np.random.uniform(0.7, 1.1, num_fraud)
    fraud_data['historical_frequency'] = np.random.uniform(3, 15, num_fraud)
    
    # 20% subtle fraud (blends in, harder to detect)
    for i in range(num_fraud):
        if np.random.rand() < 0.20:
            fraud_data['transaction_amount'][i] = np.random.uniform(800, 3500)
            fraud_data['failed_attempts'][i] = np.random.choice([0, 1])
            fraud_data['transactions_last_5min'][i] = np.random.choice([1, 2])
            fraud_data['distance_from_previous'][i] = np.random.uniform(5, 40)
            fraud_data['is_new_device'][i] = False

    df_legit = pd.DataFrame(legit_data)
    df_fraud = pd.DataFrame(fraud_data)
    df = pd.concat([df_legit, df_fraud]).sample(frac=1, random_state=seed).reset_index(drop=True)
    
    # Add timestamps (spanning last 30 days)
    end_date = datetime.datetime.now()
    start_date = end_date - datetime.timedelta(days=30)
    timestamps = [start_date + datetime.timedelta(seconds=random.randint(0, int((end_date - start_date).total_seconds()))) for _ in range(num_transactions)]
    df['timestamp'] = sorted(timestamps)
    
    return df

def main():
    parser = argparse.ArgumentParser(description="Generate synthetic transaction data for BharatSHIELD.")
    parser.add_argument('--num-transactions', type=int, default=15000, help='Total number of transactions to generate')
    parser.add_argument('--fraud-rate', type=float, default=0.03, help='Proportion of fraudulent transactions')
    parser.add_argument('--output-dir', type=str, default='data/raw', help='Directory to save the generated CSVs')
    parser.add_argument('--seed', type=int, default=42, help='Random seed for reproducibility')
    
    args = parser.parse_args()
    
    print(f"Generating {args.num_transactions} transactions with ~{args.fraud_rate*100}% fraud rate...")
    df = generate_transactions(num_transactions=args.num_transactions, fraud_rate=args.fraud_rate, seed=args.seed)
    
    base_path = Path(__file__).parent.parent
    out_dir = base_path / args.output_dir if not Path(args.output_dir).is_absolute() else Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    
    full_path = out_dir / 'transactions.csv'
    df.to_csv(full_path, index=False)
    print(f"Saved full dataset to {full_path}")
    
    demo_legit = df[df['is_fraud'] == 0].sample(n=180, random_state=args.seed)
    demo_fraud = df[df['is_fraud'] == 1].sample(n=20, random_state=args.seed)
    demo_fraud['transaction_hour'] = 2
    demo_df = pd.concat([demo_legit, demo_fraud]).sample(frac=1, random_state=args.seed).reset_index(drop=True)
    
    demo_path = out_dir / 'demo_transactions.csv'
    demo_df.to_csv(demo_path, index=False)
    print(f"Saved demo dataset to {demo_path}")
    
    print("\nData Summary:")
    print("-" * 30)
    print(f"Total Transactions: {len(df)}")
    print(f"Fraud Count: {df['is_fraud'].sum()}")
    print(f"Fraud Rate: {(df['is_fraud'].sum() / len(df)) * 100:.2f}%")

if __name__ == '__main__':
    main()
