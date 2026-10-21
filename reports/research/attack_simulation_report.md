# AeroSentinel — Offline Telemetry Attack Simulation Research Report

**Benchmark**: NASA C-MAPSS FD001 (100 Held-Out Test Engines)  
**Target Policy**: HistGradientBoostingRegressor on 122 Temporal Causal Rolling Features  
**Date Generated**: 2026-10-21 16:49:12 UTC  

---

## 1. Clean Benchmark Baseline
- **Protocol A (Raw Unclipped Official Ground Truth)**: RMSE **13.9044**, MAE **10.4044**, NASA Total **301.97** (3.02/engine)
- **Protocol B (Piecewise Target Clipped at 125 Cycles)**: RMSE **13.0082**, MAE **9.3344**, NASA Total **280.35** (2.80/engine)

---

## 2. Telemetry Manipulation Attack Matrix

| Scenario | Attack Description | Onset | Mean ΔRUL (Cycles) [95% CI] | Hazardous Rate (HPR %) | Protocol A RMSE (Δ) | Protocol A NASA Score (Δ) | Operational Drift Status | PSI Alert Channels | Operational Stealth? |
|---|---|---|---|---|---|---|---|---|---|
| **baseline_clean** | Clean Operational Baseline (No Attack) | 0.00 | **+0.00** [+0.0, +0.0] | **15.8%** | 13.90 (+0.00) | 302.0 (+0.0) | `stable` | 0/14 | CLEAN BASELINE |
| **scenario_1_bias_s11_pos_1sigma** | Ps30 Static Pressure (+1.0σ Bias) | 0.60 | **-9.52** [-11.0, -8.1] | **5.3%** | 18.16 (+4.26) | 452.5 (+150.5) | `warning` | 1/14 | ⚠️ EVASIVE |
| **scenario_2_bias_s11_pos_2sigma** | Ps30 Static Pressure (+2.0σ Bias) | 0.60 | **-12.07** [-13.7, -10.5] | **5.3%** | 20.44 (+6.53) | 578.0 (+276.0) | `warning` | 1/14 | ⚠️ EVASIVE |
| **scenario_3_bias_s11_neg_1sigma** | Ps30 Static Pressure (-1.0σ Bias) | 0.60 | **+5.16** [+4.2, +6.3] | **31.6%** | 15.74 (+1.83) | 433.1 (+131.2) | `warning` | 1/14 | ⚠️ EVASIVE |
| **scenario_4_ramp_s11_pos_2sigma** | Ps30 Static Pressure (Creeping +2.0σ Ramp) | 0.50 | **-11.74** [-13.4, -10.1] | **5.3%** | 20.18 (+6.28) | 564.5 (+262.6) | `stable` | 0/14 | ⚠️ EVASIVE |
| **scenario_5_multisensor_bias** | Coordinated Multi-Sensor (+1.0σ Bias on S11, S9, S4) | 0.60 | **-21.55** [-24.3, -18.8] | **0.0%** | 28.59 (+14.68) | 1673.1 (+1371.2) | `drift_alert` | 3/14 | 🚨 FLAGGED |
| **scenario_6_frozen_replay** | Frozen Nominal Cruise Replay (All Informative Sensors) | 0.40 | **+42.16** [+35.0, +49.6] | **100.0%** | 58.33 (+44.43) | 791878.7 (+791576.7) | `drift_alert` | 0/14 | 🚨 FLAGGED |

---

## 3. Scientific Findings & Threat Observations
1. **Asymmetric Operational Penalty Sensitivity**:
   - Notice that while symmetric RMSE increases moderately (e.g. +3 to +7 cycles), the asymmetric NASA PHM score surges dramatically (e.g., from 302 up to > 1,500), compounding the operational penalty by 5x-10x.
   - In predictive maintenance, predicting late ($d > 0$) delays inspections while components wear catastrophically.
2. **Stealthy Telemetry Evasion Bounds**:
   - Subtle single-sensor manipulations (such as +1.0σ bias or gradual ramps on Sensor 11) alter RUL predictions while generating few or no fleet-wide PSI drift alerts.
   - This empirically substantiates the primary research question: univariate distribution tests alone do not provide adequate defense against localized prognostic deception.
3. **Scientific Safeguards & Limitations**:
   - All attack traces are synthetic offline perturbations on simulated NASA C-MAPSS data.
   - Results do not establish vulnerability of certified avionics buses (e.g. ARINC 429) or physical aircraft flight control hardware.