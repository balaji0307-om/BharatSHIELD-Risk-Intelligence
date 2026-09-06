# BharatSHIELD — Dataset Evaluation & Selection Report

## 1. Executive Summary
In accordance with Architecture Decision #1, this document formally evaluates candidate fraud datasets against BharatSHIELD's real-time merchant risk intelligence requirements. 

BharatSHIELD operates in a merchant payment processing environment (e.g., UPI, Cards, NetBanking) with real-time risk scoring, explainable SHAP factors, and transaction velocity tracking. A **hybrid approach** was selected: benchmarking against real-world payment flow datasets while pairing with a calibrated domain-specific generator for Indian UPI/Fintech telemetry (velocity, device risk, impossible travel, and step-up auth flags).

---

## 2. Dataset Candidates Evaluation Matrix

| Criterion | Candidate A: Kaggle Credit Card Fraud (ULB) | Candidate B: IEEE-CIS Fraud Detection | Candidate C: PaySim Mobile Money Fraud (NTNU) |
|---|---|---|---|
| **Source / Provenance** | ULB Machine Learning Group / Worldline (European cardholders, Sept 2013) | Vesta Corporation / IEEE Computational Intelligence Society (2019) | NTNU / BDI Lab (Financial simulator based on real African mobile money logs) |
| **License** | Open Database License (ODbL) / CC BY 4.0 | Academic / Research Competition License | CC BY 4.0 |
| **Scale & Size** | 284,807 transactions, 2 days | 590,540 train transactions, 182 days | 6,362,620 transactions, 30 days (744 steps) |
| **Target Variable** | `Class` (0 = Legitimate, 1 = Fraud) | `isFraud` (0 = Legitimate, 1 = Fraud) | `isFraud` (0 = Legitimate, 1 = Fraud) |
| **Imbalance Ratio** | **0.172%** (492 frauds in 284,807) | **3.5%** (20,663 frauds in 590,540) | **0.129%** (8,213 frauds in 6.36M) |
| **Feature Visibility** | PCA-anonymized features (`V1`–`V28`), only `Time` and `Amount` are unmasked | High cardinality e-commerce fields (`DeviceType`, `DeviceInfo`, `addr1`, `card1-6`, `dist1`, `C1-14`, `M1-9`) | Semantic fields: `type` (CASH-IN, CASH-OUT, DEBIT, PAYMENT, TRANSFER), `amount`, `oldbalanceOrg`, `newbalanceOrig`, etc. |
| **Merchant Telemetry Suitability** | ⚠️ Low for explainability — PCA anonymization prevents intuitive SHAP business explanations like "New Device" or "High Velocity" | ✅ High richness, but extensive missing values (>50% across 200+ V-columns) and large memory footprint | ✅ Strong transfer/payment semantics, but lacks modern mobile device telemetry (fingerprint age, failed auth) |
| **Real-Time Latency Suitability** | ⚠️ High feature count without domain labels | ⚠️ Heavy preprocessing overhead (434 columns) | ✅ Fast scoring, clean schema |

---

## 3. Comparative Analysis & Decision

### Why Pure Public Datasets Fall Short on Merchant Explainability
1. **The PCA Problem (Kaggle ULB):** The Kaggle European Card dataset is widely cited, but features $V_1$ through $V_{28}$ are PCA principal components. When SHAP computes feature importance, outputting *"V14 contributed +24 risk points"* violates BharatSHIELD's foundational promise: **human-understandable, actionable explanations** for merchant risk officers (e.g., *"Device age < 2 days and 4 failed OTP attempts"*).
2. **The IEEE-CIS Complexity vs. Latency:** IEEE-CIS provides device and identity tables, but requires complex missing value strategies across 400+ anonymized columns (`V1-V339`), which is ill-suited for sub-50ms payment gateway risk evaluation.
3. **PaySim Strengths & Gaps:** PaySim provides realistic transactional flows (`TRANSFER`, `CASH_OUT`) and balance shifts, but lacks client-side velocity (transactions in last 5min/10min) and device fingerprint metrics.

---

## 4. Locked-In Strategy: The Hybrid Approach

BharatSHIELD adopts a **two-tier hybrid strategy**:

1. **Benchmark Validation against PaySim & ULB Principles:**
   - Class imbalance handling modeled on real-world distributions ($\approx 2.5\% - 3.5\%$ in high-risk merchant cohorts, with base rates around $0.2\%$).
   - Evaluation on non-accuracy metrics: **Precision-Recall AUC (PR-AUC)**, **False Positive Rate (FPR)**, **F1-Score**, and **Cost-Sensitive Threshold Optimization**.

2. **Domain-Calibrated Merchant Telemetry Generator (`scripts/generate_demo_data.py`):**
   - Synthesizes authentic Indian payment gateway traffic: UPI handles, RuPay/Cards, NetBanking.
   - Native behavioral & velocity feature schema:
     - **Velocity:** `transactions_last_5min`, `transactions_last_10min`, `transactions_last_1hr`, `amount_last_1hr`.
     - **Device & Auth:** `device_age_days`, `failed_attempts`, `is_new_device`, `device_transaction_count`.
     - **Location:** `is_new_location`, `location_change`, `distance_from_previous`.
     - **Behavioral deviation:** `avg_transaction_amount`, `amount_deviation`, `historical_frequency`.
   - Embeds 6 distinct real-world fraud typologies:
     1. *Velocity Attack / Card Testing* (burst transactions, small amounts, automated bot).
     2. *Large Amount Account Drain* (unusual midnight hour, new device, 5x average ticket size).
     3. *Credential Stuffing / Account Takeover* (repeated failed PIN/OTP attempts followed by sudden high-value transfer).
     4. *Impossible Travel / Location Hopping* (geographic separation physically unfeasible within elapsed time).
     5. *Amount Escalation Probe* (incremental trial payments leading to maximum limit breach).
     6. *Subtle Camouflage Fraud* (low-key fraud slipping under standard rule-based thresholds, caught by tree ensemble interactions).

---

## 5. Artifact Distinction & Data Lineage

| Data Tier | File Location | Purpose |
|---|---|---|
| **Raw Training Corpus** | `data/raw/transactions.csv` | 15,000 transactions (3% fraud) with multi-pattern distributions used to train and evaluate LR, Random Forest, and XGBoost models. |
| **Demo Stream Fixture** | `data/raw/demo_transactions.csv` | 200 curated transactions containing a pre-scheduled fraud velocity spike (02:00 AM IST) for deterministic, reproducible hackathon pitches. |
| **Engineered Training Matrices** | In-memory via `ml/src/data/` | Preprocessed with IQR outlier clipping, categorical one-hot encoding, and feature scaling with serialized transformers. |
| **Model Artifacts** | `ml/models/fraud_model.pkl` & `feature_config.json` | Trained model binary with immutable versioning, training timestamps, cross-validation metrics, and optimal decision threshold. |
