# BharatSHIELD — Dataset & Evaluation Specification

## 1. Why Synthetic Data?
In financial fraud research and merchant risk engineering, production transaction datasets are highly confidential and proprietary due to PCI-DSS, RBI guidelines, and PII protection regulations. Real-world fraud datasets (such as European credit card benchmarks) lack Indian payment contexts — specifically UPI transaction structures, IFSC/VPA velocities, festival seasonality, and RuPay/NetBanking dynamics.

BharatSHIELD synthesizes a high-fidelity Indian merchant payment ecosystem that simulates real adversarial fraud strategies without exposing customer PII.

---

## 2. Statistical Noise & Realistic Overlapping Distributions

Earlier generations of synthetic fraud datasets introduced artificial, linear separability (e.g., all fraud amounts were > ₹50,000, or all fraud occurred at 3 AM), leading to trivial 1.0000 F1 scores.

**BharatSHIELD v2 eliminates artificial separation** by introducing overlapping multivariate distributions:

1. **Transaction Amount Overlap:** 40% of fraudulent transactions are drawn directly from the legitimate amount distribution (₹500 – ₹25,000) to simulate card testing and stealth UPI attacks.
2. **Temporal Overlap:** Fraud is modeled with a 40% daytime probability (business hours in IST), reflecting modern social engineering and credential stuffing.
3. **Velocity Borderlines:** 30% of fraudulent transactions exhibit normal 5-minute velocity (0–2 transactions), avoiding simple rate-limiting traps.
4. **Credential Mismatch Overlap:** 25% of fraudulent attempts succeed on the first authentication try (simulating compromised OTP or device takeover), while 8% of legitimate transactions suffer 2–3 failed attempts due to user error.
5. **Subtle Fraud Generation:** 50% of simulated fraud transactions differ from legitimate transactions in only 1–2 features, forcing the model to detect nuanced multi-dimensional interactions rather than single red flags.
6. **False Positive Stress:** 5% of legitimate transactions are injected with suspicious signals (business travelers hopping cities, high holiday ticket sizes, new replacement phones) to measure model restraint.

---

## 3. Data Leakage Prevention (Entity Group Partitioning)

To guarantee that evaluation metrics reflect true generalization performance on unseen users:
- We utilize `GroupShuffleSplit` on `user_id` instead of naive random or stratified splits.
- All transactions from a specific user reside strictly within either Train, Validation, or Test.
- This prevents the model from memorizing specific user habits and ensures that hold-out test metrics reflect generalization to new entities.

---

## 4. Entity Graph Generation (Fraud Rings)

The synthetic engine provisions shared identifier pools to mirror organized syndicates:
- **Device Pools:** A cluster of 7 device IDs are reused across 3–6 fraudulent transactions spanning multiple distinct locations (Delhi, Mumbai, Bengaluru).
- **IP Ranges:** Realistic Indian ISP subnets (`103.15.x.x`, `49.36.x.x`) are shared across coordinated clusters.
- This enables the **Fraud Network Intelligence** module to traverse nodes and group transactions into detected attack rings.
