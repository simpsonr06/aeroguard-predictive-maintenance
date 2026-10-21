# AeroSentinel — Comprehensive Experimental Results

**Document Version**: 2.2.0  
**Status**: Verified against live reproducibility harness  
**Target Publication Venue**: International Journal for Science and Advance Research In Technology (IJSART)  
**Execution Environment**: Python 3.14.3 on Windows AMD64 | Production Model: `HistGradientBoostingRegressor`  

---

## 1. Clean Benchmark Baseline Results

Evaluated across all 100 held-out test engines in NASA C-MAPSS FD001 at their terminal in-service cutoff cycle:

| Metric | Protocol A (Raw Unclipped Official) | Protocol B (Clipped at 125 Cycles) |
|---|---|---|
| **Root Mean Squared Error (RMSE)** | **13.9044** cycles | **13.0082** cycles |
| **Mean Absolute Error (MAE)** | **10.4044** cycles | **9.3344** cycles |
| **Coefficient of Determination ($R^2$)** | **0.8880** | **0.8946** |
| **NASA Asymmetric PHM Score (Total)** | **301.97** | **280.35** |
| **NASA PHM Score / Engine** | **3.02** | **2.80** |
| **Total Test Engines** | 100 | 100 |
| **Critical Engines ($y \le 25$ cycles)** | 19 | 19 |
| **Hazardous Prediction Rate (Clean HPR)** | **15.79%** (3/19 engines) | **15.79%** (3/19 engines) |

*Artifact Source: `reports/research/baseline_metrics.csv`*

---

## 2. Model-Artifact Cryptographic Integrity Results

Tested across 11 adversarial manipulation vectors using asymmetric Ed25519 digital signatures and SHA-256 digests:

| Test Case | Manipulation Vector | Expected Outcome | Live Test Status | Security Enforcement Mechanism |
|---|---|---|---|---|
| **TC-01** | Genuine Signed Production Artifacts | Verified & Loaded | **PASS** | Ed25519 signature valid; 5 artifact hashes match |
| **TC-02** | Single-Byte Model Binary Tampering | Rejection prior to loading | **PASS** | SHA-256 hash mismatch; `joblib.load` never executed |
| **TC-03** | Single-Byte Preprocessor Tampering | Rejection prior to loading | **PASS** | SHA-256 hash mismatch; `joblib.load` never executed |
| **TC-04** | Signed Metadata Alteration | Rejection prior to loading | **PASS** | Ed25519 signature invalid for altered canonical payload |
| **TC-05** | Missing Digital Signature Block | Rejection in secure mode | **PASS** | Fail-closed policy in `AEROSENTINEL_REQUIRE_AUTH=1` |
| **TC-06** | Corrupted Digital Signature Hex | Rejection prior to loading | **PASS** | Elliptic-curve verification failure |
| **TC-07** | Malformed / Corrupted Manifest JSON | Rejection prior to loading | **PASS** | JSON parsing failure triggers fail-closed abort |
| **TC-08** | Trust Key Mismatch | Rejection prior to loading | **PASS** | Signature verification fails against configured public key |
| **TC-09** | Missing Required Artifact on Disk | Rejection prior to loading | **PASS** | Missing file check triggers fail-closed error |
| **TC-10** | Manifest Hash Rewrite Attack | Rejection prior to loading | **PASS** | Attacker lacks private key to re-sign forged manifest |
| **TC-11** | Development Mode Fallback | Allowed if hashes match | **PASS** | Tampered files still fail closed via SHA-256 checks |

*Artifact Source: `reports/research/artifact_integrity_results.csv`*

---

## 3. Synthetic Telemetry Manipulation & Attack Evasion Results

Evaluated across 100 test engines under isolated, causal feature engineering (122 features). Injected perturbations are synthetic and calibrated strictly on training statistics:

| Scenario ID | Attack Description | Onset ($\gamma$) | Mean $\Delta\text{RUL}$ [95% CI] | Hazardous Rate (HPR %) | Protocol A RMSE ($\Delta$) | Protocol A NASA Score ($\Delta$) | Operational Drift Status | PSI Alert Channels | Operational Stealth? |
|---|---|---|---|---|---|---|---|---|---|
| `baseline_clean` | Clean Operational Telemetry | 0.00 | **+0.00** [0.0, 0.0] | **15.8%** | 13.90 (+0.00) | 302.0 (+0.0) | `stable` | 0/14 | CLEAN BASELINE |
| `scenario_1_bias_s11_pos_1sigma` | Static Pressure $s_{11}$ (+1.0$\sigma$ Bias) | 0.60 | **-9.52** [-11.0, -8.1] | **5.3%** | 18.16 (+4.26) | 452.5 (+150.5) | `warning` | 1/14 | **⚠️ EVASIVE** |
| `scenario_2_bias_s11_pos_2sigma` | Static Pressure $s_{11}$ (+2.0$\sigma$ Bias) | 0.60 | **-12.07** [-13.7, -10.5] | **5.3%** | 20.44 (+6.53) | 578.0 (+276.0) | `warning` | 1/14 | **⚠️ EVASIVE** |
| `scenario_3_bias_s11_neg_1sigma` | Static Pressure $s_{11}$ (-1.0$\sigma$ Bias) | 0.60 | **+5.16** [+4.2, +6.3] | **31.6%** | 15.74 (+1.83) | 433.1 (+131.2) | `warning` | 1/14 | **⚠️ EVASIVE** |
| `scenario_4_ramp_s11_pos_2sigma` | Static Pressure $s_{11}$ (Creeping +2.0$\sigma$ Ramp) | 0.50 | **-11.74** [-13.4, -10.1] | **5.3%** | 20.18 (+6.28) | 564.5 (+262.6) | `stable` | 0/14 | **⚠️ EVASIVE** |
| `scenario_5_multisensor_bias` | Coordinated Multi-Sensor ($s_{11}, s_9, s_4$) | 0.60 | **-21.55** [-24.3, -18.8] | **0.0%** | 28.59 (+14.68) | 1,673.1 (+1,371.2) | `drift_alert` | 3/14 | 🚨 FLAGGED |
| `scenario_6_frozen_replay` | Frozen Cruise Replay (14 Sensors) | 0.40 | **+42.16** [+35.0, +49.6] | **100.0%** | 58.33 (+44.43) | 791,878.7 (+791,576.7) | `drift_alert` | 0/14 | 🚨 FLAGGED |

*Artifact Source: `reports/research/sensor_attack_results.csv`*

---

## 4. API Security Hardening & Input Bounds Verification

Tested against the FastAPI REST interface:

| Case ID | Interface / Endpoint | Test Vector | Response Code | Status | Hardening Mechanism |
|---|---|---|---|---|---|
| **SEC-01** | `GET /api/security/status` | Authenticated state query | 200 OK | **PASS** | Validates Ed25519 parameters & fail-closed mode |
| **SEC-02** | `GET /api/security/attack-simulation` | Simulation results query | 200 OK | **PASS** | Delivers verified simulation artifacts |
| **SEC-03** | `POST /api/predict` | `engine_id: 0` | 422 Unprocessable | **PASS** | Pydantic `Field(ge=1)` validation |
| **SEC-04** | `POST /api/predict` | `engine_id: -5` | 422 Unprocessable | **PASS** | Pydantic `Field(ge=1)` validation |
| **SEC-05** | `POST /api/predict` | `engine_id: 101` | 422 Unprocessable | **PASS** | Pydantic `Field(le=100)` validation |
| **SEC-06** | `POST /api/predict` | `cutoff_cycle: 0` | 422 Unprocessable | **PASS** | Pydantic `Field(ge=1)` validation |
| **SEC-07** | `POST /api/predict` | Empty JSON `{}` | 422 Unprocessable | **PASS** | Required field enforcement |
| **SEC-08** | `POST /api/predict` | Corrupted JSON syntax | 422 Unprocessable | **PASS** | Fast parser error handling |
| **SEC-09** | `GET /api/engines` | `critical_threshold: 2.0` | 422 Unprocessable | **PASS** | Query parameter range `ge=5.0` |
| **SEC-10** | `GET /api/engines/999` | 404 Response Audit | Clean JSON Detail | **PASS** | Zero Python traceback leakage in body |
| **SEC-11** | Global Middleware | Response Header Audit | `X-Response-Time-Ms` | **PASS** | Zero private keys or secrets in headers |
| **SEC-12** | Model Failure Simulation | Prediction during degraded state | 503 Service Unavailable | **PASS** | Fail-closed rejection when model unauthenticated |

*Artifact Source: `reports/research/api_security_results.csv`*

---

## 5. Operational Latency and Overhead Microbenchmarks

Measured over $N=100$ warm-up isolated repetitions on AMD64 hardware:

| Benchmark Name | Category | Mean Latency | Median Latency | P95 Latency | Repetitions |
|---|---|---|---|---|---|
| **Ed25519 Signature Verification** | Cryptographic Security | **0.11 ms** | **0.10 ms** | **0.16 ms** | 100 |
| **SHA-256 Digest Verification (5 Files)** | Artifact Integrity | **15.34 ms** | **14.93 ms** | **17.59 ms** | 100 |
| **Model Deserialization (`joblib.load`)** | Model Loading | **9.56 ms** | **9.42 ms** | **11.35 ms** | 100 |
| **Total Verified Pipeline Startup** | End-to-End Startup | **24.83 ms** | **24.56 ms** | **26.71 ms** | 100 |
| **Feature Engineering (13,096 cycles)** | Preprocessing | **142.27 ms** | **137.60 ms** | **169.04 ms** | 30 |
| **Single-Engine RUL Inference** | Prognostic Inference | **1.62 ms** | **1.34 ms** | **2.67 ms** | 100 |
| **Fleet-Wide (100 Engines) Inference** | Prognostic Inference | **1.47 ms** | **1.23 ms** | **2.63 ms** | 100 |
| **Covariate Drift Evaluation (14 Sensors)** | Drift Monitoring | **103.23 ms** | **102.76 ms** | **107.83 ms** | 20 |

*Artifact Source: `reports/research/performance_benchmarks.csv`*

---

## 6. Key Scientific Findings

1. **Sub-Millisecond Cryptographic Security**: Pure Ed25519 asymmetric signature verification introduces only **0.11 ms** of latency, rendering cryptographic supply-chain authentication virtually zero-overhead in production environments.
2. **The Univariate Drift Blindness Phenomenon**: Single-sensor bias and creeping ramp attacks (Scenarios 1, 2, 3, and 4) alter predicted RUL by up to 12.1 cycles while generating **0 or 1 alert channels**, allowing them to evade fleet-level operational drift detection.
3. **Catastrophic Failure Concealment**: Replay attacks that freeze telemetry at early nominal cruise values achieve a **100% Hazardous Prediction Rate (HPR)** on critical engines and cause the asymmetric NASA PHM score to surge by over 2,600x (from 302 to 791,878).
4. **Censoring Asymmetry in Drift Baselines**: Evaluating test telemetry against training data produces an immediate false positive on clean data due to the inherent difference between complete run-to-failure and in-service censored trajectories.
