# BharatSHIELD — REST API Specification

Base URL: `http://localhost:8000` (Swagger UI at `http://localhost:8000/docs`)

---

## 1. Authentication & Security
- Scheme: `Bearer <JWT_TOKEN>` via `Authorization` header.
- Endpoint: `POST /api/auth/login` and `POST /api/auth/register`.
- Role Isolation: Each merchant can only inspect transactions, alerts, and metrics assigned to their `merchant_id`.

---

## 2. Transactions & Risk Scoring

### `POST /api/transactions/score`
Evaluate and persist a single transaction in real time.

**Request Body:**
```json
{
  "merchant_id": "MER_razorpay_001",
  "transaction_amount": 85000.0,
  "transaction_hour": 2,
  "transaction_day": 3,
  "payment_method": "UPI",
  "device_age_days": 1,
  "failed_attempts": 5,
  "transactions_last_5min": 8,
  "transactions_last_10min": 12,
  "transactions_last_1hr": 25,
  "amount_last_1hr": 140000.0,
  "is_new_device": true,
  "is_new_location": true,
  "device_transaction_count": 2,
  "avg_transaction_amount": 12000.0,
  "amount_deviation": 7.08,
  "historical_frequency": 2.1,
  "location_change": 4,
  "distance_from_previous": 1250.0
}
```

**Response (200 OK):**
```json
{
  "transaction_id": "8fa160de-b23c-4b6b-a25e-3c25bca253e9",
  "status": "HOLD_FOR_REVIEW",
  "fraud_probability": 0.892,
  "risk_score": 88,
  "risk_level": "CRITICAL",
  "recommended_action": {
    "action": "Hold for Review",
    "description": "Block transaction immediately and dispatch to risk analyst queue.",
    "urgency": "CRITICAL",
    "details": [
      "Unusual midnight velocity detected (+28 pts)",
      "New device with 5 failed authentication attempts (+32 pts)",
      "Impossible geographic distance from last active city (+25 pts)"
    ]
  },
  "risk_factors": [
    {
      "feature": "is_new_device",
      "display_name": "New Device Detected",
      "contribution": 32.4,
      "direction": "increases_risk",
      "value": true
    },
    {
      "feature": "failed_attempts",
      "display_name": "Failed Authentication Attempts",
      "contribution": 25.1,
      "direction": "increases_risk",
      "value": 5
    }
  ],
  "audit_log_id": "aud_018f237a_91ab",
  "timestamp": "2026-09-06T00:25:00+05:30"
}
```

### `GET /api/transactions`
List transactions with optional filtering and pagination.
- Query parameters: `page`, `page_size`, `risk_level`, `merchant_id`, `start_date`, `end_date`.

### `GET /api/transactions/{id}`
Retrieve single transaction deep-dive including risk factors, device history, and linked transactions.

### `GET /api/transactions/{id}/related`
Retrieve heuristic matches (shared device fingerprint, IP/location within 6 hours, or rapid velocity clusters).

---

## 3. Analytics & Model Performance

### `GET /api/analytics/overview`
Summary KPI tiles:
- `total_transactions`
- `fraud_detected_count`
- `high_risk_count`
- `critical_risk_count`
- `average_risk_score`

### `GET /api/analytics/trends`
Hourly/Daily aggregated risk and volume time-series.

### `GET /api/analytics/model`
Real computed model evaluation metrics directly from the serialized training artifact:
- `model_version`, `model_name`, `training_date`
- `precision`, `recall`, `f1_score`, `auc_roc`, `false_positive_rate`
- `confusion_matrix`
- `feature_importance`

---

## 4. Alerts & Anomaly Intelligence

### `GET /api/alerts`
List fraud spikes, rapid velocity anomalies, and critical threshold breaches.

### `PUT /api/alerts/{id}/acknowledge`
Acknowledge an alert and record reviewer notes in the audit trail.

---

## 5. AI Risk Assistant

### `POST /api/assistant/ask`
Strictly read-only, defense-constrained query layer.
- **Accepted scopes:** Transaction risk factor inquiries, merchant daily risk summaries, explanation of high risk clusters.
- **Guardrail guarantee:** Zero capability to execute funds transfer, release holds, or alter system state.
