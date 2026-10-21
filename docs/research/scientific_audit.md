# AeroSentinel Phase D — Scientific Audit of Datasets & Experiments

**Date**: October 21, 2026  
**Auditor**: Senior Experimental Scientist & ML Security Researcher  
**Benchmark**: NASA C-MAPSS FD001 Turbofan Run-to-Failure Benchmark  
**Dataset Provenance**: NASA Ames Prognostics Center of Excellence (PCoE)  

---

## 1. Dataset Provenance and Lineage Integrity

The empirical experiments are executed on the official NASA C-MAPSS FD001 dataset files located in `data/raw/`:

| Dataset File | Exact SHA-256 Checksum | Description | Structure |
|---|---|---|---|
| `train_FD001.txt` | `963b5e22825b34d8b21c69e1aeb4af3e647050eb672ee8834ba4b5d91d2de0f8` | 100 training engines run to complete physical failure ($RUL = 0$). | 20,631 rows, 26 space-separated columns (Engine ID, Cycle, 3 Settings, 21 Sensors). |
| `test_FD001.txt` | `3cda7109ce17bafb5443f2ac926cfcf88154b941b8c4cf95eb55d1ddd6f52851` | 100 held-out test engines monitored during in-service operation and censored at arbitrary cutoff cycles $T_i$ prior to failure. | 13,096 rows, 26 space-separated columns. Cutoff cycles range from 31 to 303. |
| `RUL_FD001.txt` | `a19c8ec94931949d0485bdc35118206e9c81c4547b422efb9cf86f4ceddbceca` | 100 official ground-truth Remaining Useful Life labels corresponding to final observed cycles of the 100 test engines. | 100 integer values ranging from 7 to 145 cycles. |

All SHA-256 digests match the cryptographically signed `models/model_manifest.json` exactly. Source raw data files remain read-only and unmodified.

---

## 2. Independent Reproduction of Clean Baseline Protocols

The champion model (`HistGradientBoostingRegressor`) operating on 122 temporal causal rolling features was evaluated against the 100 held-out test engines at their terminal cutoff cycle $T_i$.

Both evaluation protocols were recomputed independently:

### Protocol A: Raw Unclipped Official Test Labels
- **Target Definition**: $y_i = \text{RUL\_FD001}[i]$ (unmodified NASA PHM 2008 ground truth).
- **Verified Metrics**:
  - **RMSE**: **13.9044**
  - **MAE**: **10.4044**
  - **$R^2$**: **0.8880**
  - **NASA Total Score**: **301.97**
  - **NASA Score / Engine**: **3.02**

### Protocol B: Target Clipped at 125 Cycles
- **Target Definition**: $y_i^* = \min(y_i, 125)$ (aligns evaluation with the training target policy).
- **Verified Metrics**:
  - **RMSE**: **13.0082**
  - **MAE**: **9.3344**
  - **$R^2$**: **0.8946**
  - **NASA Total Score**: **280.35**
  - **NASA Score / Engine**: **2.80**

Both results match the certified values recorded in `models/model_manifest.json` to 4 decimal places.

---

## 3. Scientific Audit of Covariate Drift Baselines

A crucial scientific audit finding relates to the choice of reference distribution for operational drift detection:

### 3.1 The Censoring Asymmetry Phenomenon
- In `train_FD001.txt`, all 100 engines operate until physical failure ($RUL = 0$). Consequently, the training distribution contains a high proportion of severely degraded, high-vibration, high-temperature sensor readings.
- In `test_FD001.txt`, trajectories are censored at arbitrary operating points before failure.
- When `test_FD001.txt` (clean) is compared directly against `train_FD001.txt` using two-sample KS and PSI tests:
  - **8 out of 14** informative sensors exhibit $PSI \ge 0.25$ (`drift_alert`).
  - **6 out of 14** informative sensors exhibit $0.10 \le PSI < 0.25$ (`warning`).
  - Overall status is flagged as **`drift_alert`** on completely benign, unmanipulated test data.
- **Scientific Implication**: Using training data as the reference baseline yields an unacceptable **100% false-positive rate** for operational fleet monitoring due to run-to-failure censoring differences. 

### 3.2 Dual-Baseline Protocol Requirement
To produce scientifically defensible findings, drift detectors must be evaluated under two distinct reference modes:
1. **Reference A (Training Baseline)**: Measures divergence from the initial model calibration distribution ($P(X_{\text{train}})$ vs $P(X_{\text{eval}})$).
2. **Reference B (Clean Operational Test Baseline)**: Measures divergence from clean operational telemetry ($P(X_{\text{clean\_test}})$ vs $P(X_{\text{attacked\_test}})$), isolating the specific impact of synthetic sensor manipulation.

---

## 4. Formalization of the Hazardous Prediction Rate (HPR)

### 4.1 Prior Implementation Defect
In earlier scripts, HPR was computed using an ad-hoc heuristic:
$$\text{HazardousCount} = \sum_{i \in \text{Critical}} \mathbb{I}((\hat{y}_i^{\text{attack}} - \hat{y}_i^{\text{clean}}) > 15)$$
where $\text{Critical} = \{i : y_i \le 25\}$.
- **Defect**: This heuristic omitted cases where an engine with true RUL of 18 was shifted from 20 to 28 cycles ($\Delta = +8 \le 15$). Despite delaying maintenance past the critical safety threshold, it was counted as safe.

### 4.2 Canonical Formulation
We formalize the **Hazardous Prediction Rate (HPR)** as:
$$\text{HPR} = \frac{\sum_{i \in \text{Critical}} \mathbb{I}(\hat{y}_i^{\text{attack}} > \theta_{\text{crit}})}{|\text{Critical}|} \times 100\%$$
where:
- $\theta_{\text{crit}} = 25$ cycles (the established maintenance priority critical cutoff).
- $\text{Critical} = \{i \mid y_i \le \theta_{\text{crit}}\}$.
- In NASA C-MAPSS FD001, exactly **19 out of 100 test engines** satisfy $y_i \le 25$.

### 4.3 Empirical Comparison

| Scenario | Attack Type | Mean $\Delta\text{RUL}$ | Clean Baseline HPR | Old Heuristic HPR | Canonical HPR |
|---|---|---|---|---|---|
| Clean Baseline | None | 0.00 c | — | 0.0% | **15.8%** (3/19) |
| Scenario 1 | $s_{11}$ (+1.0$\sigma$ Bias) | -9.52 c | 15.8% | 0.0% | **5.3%** (1/19) |
| Scenario 2 | $s_{11}$ (+2.0$\sigma$ Bias) | -12.07 c | 15.8% | 0.0% | **5.3%** (1/19) |
| Scenario 3 | $s_{11}$ (-1.0$\sigma$ Bias) | +5.16 c | 15.8% | 5.3% | **31.6%** (6/19) |
| Scenario 4 | $s_{11}$ (+2.0$\sigma$ Ramp) | -11.74 c | 15.8% | 0.0% | **5.3%** (1/19) |
| Scenario 5 | Coordinated Multi-Sensor | -21.55 c | 15.8% | 0.0% | **0.0%** (0/19) |
| Scenario 6 | Frozen Nominal Replay | +42.16 c | 15.8% | 100.0% | **100.0%** (19/19) |

**Key Finding**: In Scenario 3 (negative bias on static pressure), the canonical HPR reveals that **31.6% of critical engines** are falsely classified as non-critical, compared to only 5.3% under the old heuristic. In Scenario 6, **100% of critical engines** are falsely predicted healthy.
