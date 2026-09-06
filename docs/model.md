# BharatSHIELD — Machine Learning Pipeline & Model Evaluation

## 1. Machine Learning Pipeline Architecture

The BharatSHIELD fraud detection engine follows a production-grade ML lifecycle designed for high throughput, class-imbalanced fraud detection, and sub-second explainability.

```
Raw Data Ingestion (transactions.csv)
       │
       ▼
Preprocessing & Data Hygiene
  ├── Missing value imputation (numeric: median, categorical: mode)
  ├── Outlier capping via Interquartile Range (IQR)
  └── Categorical encoding (One-Hot on payment methods, bool->int)
       │
       ▼
Domain Feature Engineering
  ├── Transaction: amount bins, hour bins, weekend flags, log amount
  ├── Velocity: 5min/10min/1hr transaction counts, velocity acceleration ratios
  └── Behavioral: deviation from merchant/user average, composite device & location risk scores
       │
       ▼
Stratified Train / Val / Test Partition (70% / 15% / 15%)
       │
       ▼
Class Imbalance Mitigation
  ├── scale_pos_weight (Negative / Positive ratio) for XGBoost
  ├── class_weight='balanced' for Tree ensembles & Logistic Regression
  └── SMOTE synthetic oversampling benchmarking
       │
       ▼
Model Comparison Tournament
  ├── Logistic Regression (Baseline)
  ├── Random Forest (Ensemble baseline)
  └── XGBoost Classifier (Gradient boosted trees - Winner)
       │
       ▼
Optimal Threshold Discovery
  └── Sweep thresholds in [0.1, 0.9] to maximize F1-score & mitigate false-positive business friction
       │
       ▼
Evaluation on Held-Out Test Set (Unseen Data)
  └── Strict evaluation: Precision, Recall, F1, AUC-ROC, PR-AUC, FPR
       │
       ▼
Artifact Serialization
  ├── Serialized model binary (`ml/models/fraud_model.pkl`)
  ├── Scaler transformer (`ml/models/scaler.pkl`)
  └── Feature & Evaluation Registry (`ml/models/feature_config.json`)
```

---

## 2. Feature Definitions & Signals

| Feature Name | Category | Description | Rationale |
|---|---|---|---|
| `transaction_amount` | Transaction | Gross transaction value in INR | Fraudulent attempts frequently test high limits or micro-probe. |
| `amount_log` | Transaction | Natural logarithm of transaction amount | Stabilizes extreme variance in ticket sizes. |
| `transaction_hour` | Transaction | Hour of transaction in IST (0–23) | Legitimate UPI traffic peaks during day; automated fraud surges 1:00 AM–5:00 AM. |
| `transactions_last_5min` | Velocity | Transaction count from same user/device in last 5m | Detects card-testing bots and rapid-fire script attacks. |
| `velocity_ratio_5_10` | Velocity | Ratio of 5-min to 10-min transaction counts | Captures sudden acceleration in payment frequency. |
| `device_age_days` | Device | Days since device fingerprint first seen | Brand new devices have significantly higher risk probability. |
| `failed_attempts` | Device / Auth | Consecutive failed PIN/OTP/CVV attempts | Strong indicator of credential stuffing or stolen instrument. |
| `distance_from_previous` | Location | Kilometers between current and prior geo-IP | Flags impossible travel anomalies (e.g., Mumbai to Delhi in 10 minutes). |
| `amount_deviation` | Behavioural | Ratio of transaction amount to historical mean | Identifies anomalous high-value spikes relative to normal habits. |
| `device_risk_score` | Composite | Blended index of age, novelty, and device history | Normalized 0–1 score capturing overall device trust. |
| `location_risk_score` | Composite | Blended index of novelty, change count, and distance | Normalized 0–1 score capturing geographic anomaly. |

---

## 3. Evaluation Principles (Non-Fabricated Metrics)

BharatSHIELD strictly prohibits synthetic or hardcoded evaluation metrics.
- All metrics reported in the UI (`/analytics`) and API (`/api/analytics/model`) are dynamically loaded from `ml/models/feature_config.json`, generated during test-set evaluation.
- Primary Optimization Metric: **$F_1$-score** and **PR-AUC**, balancing fraud detection recall against merchant false-positive friction costs.
