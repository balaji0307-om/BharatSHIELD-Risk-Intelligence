# BharatSHIELD Architecture Specification

```mermaid
flowchart TB
    subgraph ClientLayer["Presentation & Merchant Layer (React 18 + Vite + Tailwind)"]
        UI_Dash["Merchant Dashboard (/dashboard)"]
        UI_Txn["Transaction Stream & Table (/transactions)"]
        UI_Detail["Deep Dive & Explainability View (/transactions/:id)"]
        UI_Alerts["Fraud Spike & Velocity Alerts (/alerts)"]
        UI_Analytics["Model & Financial Metrics (/analytics)"]
        UI_Assistant["Constrained AI Risk Assistant (/assistant)"]
    end

    subgraph APILayer["FastAPI Gateway (Python 3.11/3.12)"]
        AuthMid["JWT Auth & Merchant Tenant Isolation"]
        RateLimiter["Adaptive Rate Limiting"]
        RouterTxn["/api/transactions Router"]
        RouterRisk["/api/risk Router"]
        RouterAnalytics["/api/analytics Router"]
        RouterAlerts["/api/alerts Router"]
        RouterAssistant["/api/assistant Router (Defense Guardrailed)"]
    end

    subgraph CoreRiskEngine["BharatSHIELD Risk Engine"]
        Engine["risk_engine.py Orchestrator"]
        FeaturePipe["Feature Engineering Pipeline\n(Velocity, Device, Behavioural)"]
        MLModel["XGBoost Classifier (Class Weighted / SMOTE)"]
        SHAP["SHAP TreeExplainer\n(Explainability Layer)"]
        Anomaly["Anomaly & Velocity Spike Monitor\n(Z-Score / Moving Window)"]
        Rules["Heuristic Decision Matrix\n(Allow / Verify / Step-up / Hold)"]
    end

    subgraph DataStorage["Data Persistence Layer"]
        DB[(PostgreSQL Primary / SQLite Fallback)]
        AuditLog[(Immutable Audit Log Trail)]
        ModelStore[(Model Artifacts & Version Registry)]
    end

    ClientLayer -->|REST API Requests / JWT| APILayer
    APILayer --> CoreRiskEngine
    CoreRiskEngine --> FeaturePipe
    FeaturePipe --> MLModel
    MLModel --> SHAP
    MLModel --> Anomaly
    MLModel --> Rules
    Rules --> Engine
    Engine --> AuditLog
    Engine --> DB
    ModelStore --> MLModel
```

## System Components

### 1. Presentation Tier (React + Vite)
- **Real-Time Visualization:** Recharts-driven risk score histograms, 24-hour volume trend, and merchant risk exposure charts.
- **Explainability Display:** Horizontal contribution bar chart directly visualizing positive and negative SHAP force values converted to plain language risk points.
- **Investigation Drilldown:** Detailed breakdown of device lineage, IP/geographic distance hops, velocity surges, and related merchant transactions.

### 2. Application & API Tier (FastAPI)
- Modular routers strictly segregated by business domain.
- Pydantic v2 schemas providing strict compile-time and runtime validation.
- Standardized error envelopes with request traceability.
- Asynchronous database operations with SQLAlchemy 2.0.

### 3. Intelligence Tier
- **Multi-Factor Feature Extractor:** Computes 5m, 10m, 1h velocity ratios, amount-to-historical deviation, and composite device trust scores.
- **Ensemble Classifier:** Optimized XGBoost model trained on class-imbalanced transaction telemetry.
- **SHAP Attribution:** Local feature attribution calculated via TreeExplainer on every incoming transaction inference pass.
- **Fraud Spike Monitor:** Rolling baseline z-score calculation comparing immediate merchant volume and high-risk ratios against historical averages.

### 4. Persistence & Audit Tier
- **Relational Stores:** `merchants`, `users`, `transactions`, `risk_scores`, `risk_factors`, `alerts`, `risk_cases`.
- **Immutable Audit Trail:** Append-only `audit_logs` storing original payload, raw score, computed explanation factors, recommended action, and decision timestamp.
