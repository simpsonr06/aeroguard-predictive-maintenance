# Aircraft Engine Remaining Useful Life (RUL) - Model Evaluation Report
**Dataset**: NASA C-MAPSS FD001  
**Cross-Validation Strategy**: 5-Fold Engine-Level GroupKFold (Zero cross-engine leakage)  
**Piecewise RUL Threshold**: 125 cycles  
**Total Features Engineered**: 122  
**Model Selection Basis**: Cross-Validation Full-Trajectory RMSE (No test set snooping)  
**Selected Production Model**: **HistGradientBoosting**  

---

## 1. Engine-Level 5-Fold Cross-Validation: Full Trajectory (Continuous Monitoring)
Evaluates continuous degradation tracking across all operational cycles (~4,126 cycles per fold, 20,631 total):

| Model | Full CV RMSE | Full CV MAE | Full CV R² | CV NASA Sum (Per Fold) | CV NASA Per Sample |
|---|---|---|---|---|---|
| **Dummy (Mean Baseline)** | 41.67 ± 0.00 | 36.97 ± 0.00 | 0.000 ± 0.000 | 1271029.3 | **308.04** |
| **Ridge Regression** | 16.21 ± 1.55 | 12.76 ± 1.45 | 0.847 ± 0.030 | 18440.0 | **4.47** |
| **Random Forest** | 14.05 ± 1.21 | 9.98 ± 1.01 | 0.885 ± 0.020 | 17959.9 | **4.35** |
| **HistGradientBoosting** | 13.76 ± 1.57 | 9.68 ± 1.10 | 0.890 ± 0.025 | 16213.2 | **3.93** |

---

## 2. Engine-Level 5-Fold Cross-Validation: In-Service Cutoff Prognosis (Pre-Failure)
Evaluates single-point in-service inspection on held-out validation engines truncated prior to failure ($t \sim \text{Uniform}(0.40, 0.85) \times T_{\text{max}}$).
**Note**: Designed exclusively from training data without consulting official test labels. Evaluated strictly against the actual ground-truth remaining cycles at that cutoff ($T_{\text{max}} - t_{\text{cutoff}}$).

| Model | Cutoff CV RMSE | Cutoff CV MAE | Cutoff CV R² | Cutoff NASA Sum (20 Engines) | Cutoff NASA Per Engine |
|---|---|---|---|---|---|
| **Dummy (Mean Baseline)** | 30.03 ± 2.27 | 26.00 ± 2.38 | -0.134 ± 0.140 | 685.7 | **34.29** |
| **Ridge Regression** | 21.39 ± 1.81 | 18.80 ± 1.63 | 0.420 ± 0.106 | 168.7 | **8.44** |
| **Random Forest** | 19.69 ± 1.99 | 15.77 ± 1.70 | 0.511 ± 0.086 | 209.6 | **10.48** |
| **HistGradientBoosting** | 19.52 ± 2.84 | 16.09 ± 2.54 | 0.524 ± 0.080 | 169.2 | **8.46** |

---

## 3. Engine-Level 5-Fold Cross-Validation: Catastrophic Failure-Point Detection (RUL = 0)
Evaluates prediction accuracy strictly at the catastrophic failure point ($t = T_{\text{max}}$) where true RUL is identically 0.
*(Note: This measures end-of-life failure detection accuracy; it does NOT evaluate in-service pre-failure prognosis).* 

| Model | Failure CV RMSE | Failure CV MAE | Failure CV R² | Failure NASA Sum (20 Engines) | Failure NASA Per Engine |
|---|---|---|---|---|---|
| **Dummy (Mean Baseline)** | 86.83 ± 0.01 | 86.83 ± 0.01 | 0.000 ± 0.000 | 118006.1 | **5900.31** |
| **Ridge Regression** | 1.56 ± 1.22 | 0.58 ± 0.53 | 0.200 ± 0.400 | 1.7 | **0.08** |
| **Random Forest** | 2.43 ± 0.25 | 2.14 ± 0.19 | 0.000 ± 0.000 | 5.0 | **0.25** |
| **HistGradientBoosting** | 3.35 ± 0.27 | 2.88 ± 0.24 | 0.000 ± 0.000 | 7.1 | **0.35** |

---

## 4. Official FD001 Held-Out Test Set Metrics (100 Test Engines at Pre-Failure Cutoff)

Evaluated on the 100 test engines strictly at their final observed in-service cycle against official `RUL_FD001.txt` ground truth:

| Model | Official Test RMSE (Unclipped) | Test RMSE (Clipped @ 125) | Official Test MAE | Official Test R² | Official Test NASA Total | Official Test NASA / Engine |
|---|---|---|---|---|---|---|
| **Dummy (Mean Baseline)** | **43.07** | 41.94 | 35.90 | -0.074 | **33629.2** | **336.29** |
| **Ridge Regression** | **17.42** | 16.41 | 14.40 | 0.824 | **458.5** | **4.59** |
| **Random Forest** | **14.44** | 13.59 | 10.77 | 0.879 | **351.9** | **3.52** |
| **HistGradientBoosting** | **13.90** | 13.01 | 10.40 | 0.888 | **302.0** | **3.02** |

---

## 5. Methodological Analysis & Clipping Policy
1. **Target Clipping Policy**:
   - Training models on piecewise linear RUL clipped at 125 cycles reflects the physical reality that early in engine life, degradation has not yet begun.
   - In the official test set, true RUL values range up to 145 cycles. Because models predict $\le 125$, engines with true RUL between 125 and 145 incur an artificial residual of at least $(y - 125)$.
   - When evaluated against the piecewise linear target (`test_rmse_clipped`), HistGradientBoosting achieves **13.01 cycles RMSE**.
   - When evaluated against the raw, unclipped competition ground truth (`test_rmse_official`), it achieves **13.90 cycles RMSE**.
2. **Distinct Evaluation Regimes**:
   - **Continuous Trajectory CV (RMSE 13.76)** evaluates operational tracking across the entire lifecycle.
   - **In-Service Cutoff CV (RMSE 19.52)** evaluates single-point inspection on truncated trajectories without failure symptoms.
   - **Failure-Point CV (RMSE 3.35)** evaluates detection of catastrophic end-of-life breakdown where physical signals have spiked.
   - **Official Test Set (RMSE 13.90)** is the held-out NASA C-MAPSS competition benchmark.
3. **Zero Test-Label Contamination**:
   - Cross-validation design, cutoff selection, feature transformation, and model selection were performed strictly without reading official test labels.
4. **Cutoff-Schedule Limitation**:
   - The in-service cutoff validation protocol selects cutoff cycles by sampling an operational fraction $u_i \sim \text{Uniform}(0.40, 0.85)$ deterministically per engine. While this guarantees zero test-label leakage and tests model behavior on truncated trajectories prior to failure, it operates under the assumption of a uniform in-service inspection distribution.
   - In real-world commercial airline fleet operations, maintenance inspections (such as Line checks, A-checks, and C-checks) follow fixed flight-hour intervals (e.g. every 400-600 flight hours) or condition-based trigger thresholds (e.g. exceedance alerts on EGT or vibration) rather than uniform operational percentages. Consequently, operational performance in deployment may vary depending on the airline's specific inspection schedule.

## 6. Persisted Artifacts
- `models/best_model.joblib`: Production model artifact (HistGradientBoosting)
- `models/preprocessor.joblib`: Fitted feature pipeline and scaler
- `models/model_registry.json`: JSON performance registry
- `reports/figures/model_test_predictions.png`: Actual vs Predicted scatter plots
- `reports/figures/model_residuals.png`: Error distribution density curves
- `reports/figures/feature_importances.png`: Top 20 predictive features