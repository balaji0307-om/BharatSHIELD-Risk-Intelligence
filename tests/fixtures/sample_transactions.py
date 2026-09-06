"""
Sample test fixtures representing different transaction risk profiles.
"""

LEGITIMATE_TRANSACTION = {
    "merchant_id": "MER_razorpay_001",
    "transaction_amount": 1250.0,
    "payment_method": "UPI",
    "transaction_hour": 14,
    "transaction_day": 2,
    "device_age_days": 180,
    "failed_attempts": 0,
    "transactions_last_5min": 1,
    "transactions_last_10min": 1,
    "transactions_last_1hr": 3,
    "amount_last_1hr": 2500.0,
    "is_new_device": False,
    "is_new_location": False,
    "device_transaction_count": 85,
    "avg_transaction_amount": 1200.0,
    "amount_deviation": 1.04,
    "historical_frequency": 2.0,
    "location": "Mumbai",
    "distance_from_previous": 2.5
}

CRITICAL_FRAUD_TRANSACTION = {
    "merchant_id": "MER_razorpay_001",
    "transaction_amount": 185000.0,
    "payment_method": "Credit Card",
    "transaction_hour": 3,
    "transaction_day": 1,
    "device_age_days": 1,
    "failed_attempts": 6,
    "transactions_last_5min": 14,
    "transactions_last_10min": 22,
    "transactions_last_1hr": 48,
    "amount_last_1hr": 390000.0,
    "is_new_device": True,
    "is_new_location": True,
    "device_transaction_count": 1,
    "avg_transaction_amount": 8000.0,
    "amount_deviation": 23.1,
    "historical_frequency": 1.2,
    "location": "Kolkata",
    "distance_from_previous": 1950.0
}
