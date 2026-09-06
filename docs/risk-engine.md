# BharatSHIELD — Risk Engine & Explainability Specification

## 1. Risk Scoring Mechanics

### Probability to Risk Score Transformation
Rather than presenting raw probabilities (which cluster near 0 for imbalanced fraud rates), BharatSHIELD utilizes a calibrated logistic scaling function:

$$Score = \text{round}\left(100 \times \frac{1}{1 + e^{-k \cdot (P - \tau)}}\right)$$

Where:
- $P \in [0, 1]$: Raw fraud probability output from the XGBoost booster.
- $\tau$: Empirically discovered optimal decision threshold (maximizing $F_1$ or cost utility).
- $k$: Steepness hyperparameter (calibrated to $k = 10.0$) ensuring intuitive spread across the 0–100 spectrum.

### 2. Risk Bands & Automated Action Policies

| Band | Risk Level | Score Range | Action | Operational Protocol |
|---|---|---|---|---|
| **Band 1** | `LOW` | 0 – 24 | **ALLOW** | Frictionless straight-through processing (STP); silent background telemetry. |
| **Band 2** | `MEDIUM` | 25 – 49 | **VERIFY** | Lightweight passive check (silent device fingerprint verification, silent OTP/SMS push). |
| **Band 3** | `HIGH` | 50 – 74 | **STEP-UP AUTH** | Mandatory step-up authentication (biometric confirmation, 2-Factor token). |
| **Band 4** | `CRITICAL` | 75 – 100 | **HOLD FOR REVIEW** | Immediate transaction hold; alert dispatched to merchant risk queue; funds frozen pending risk analyst review. |

---

## 3. Explainability Layer: SHAP to Plain-Language Translation

BharatSHIELD guarantees that **no risk score is emitted without an itemized explanation**.

### Translation Pipeline
1. **TreeExplainer Evaluation:** For an inference vector $\mathbf{x}$, SHAP calculates the marginal attribution $\phi_i$ for each feature $i \in \{1, \dots, M\}$ such that:
   $$f(\mathbf{x}) = \phi_0 + \sum_{i=1}^{M} \phi_i$$
2. **Attribution Normalization:** Feature impacts are normalized and scaled into intuitive "Risk Points" ($\Delta \text{Pts}_i \propto \phi_i$).
3. **Semantic Mapping:** Abstract technical feature keys are mapped to domain-specific risk statements:
   - `is_new_device=True` $\rightarrow$ *"New Device Detected (+32 pts)"*
   - `failed_attempts >= 3` $\rightarrow$ *"Multiple Failed Authentication Attempts (+24 pts)"*
   - `distance_from_previous > 500km` $\rightarrow$ *"Impossible Travel / Velocity Hop (+28 pts)"*
   - `transactions_last_5min > 5` $\rightarrow$ *"High Velocity Transaction Burst (+21 pts)"*
   - `amount_deviation > 3.0` $\rightarrow$ *"Ticket Size Exceeds Baseline by 300% (+19 pts)"*

4. **Consistency Invariant:**
   Unit tests guarantee that positive risk point adjustments directionally correlate with the assigned risk band, preventing contradictory UI states.
