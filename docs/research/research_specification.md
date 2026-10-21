# AeroSentinel: Research Specification & Formal Problem Formulation

**Document Identifier:** `DOC-RES-001`  
**Version:** `1.0.0`  
**Classification:** Academic Research & Security Engineering  
**Target Publication Venue:** International Journal for Science and Advance Research In Technology (IJSART)  
**Evaluation Setting:** NASA C-MAPSS Turbofan Degradation Dataset (FD001 Sub-dataset)  

---

## 1. Executive Summary & Problem Statement

Prognostics and Health Management (PHM) systems deploy Machine Learning (ML) regressors to estimate the Remaining Useful Life (RUL) of safety-critical turbofan engines from continuous multi-channel sensor telemetry. While extensive research optimizes point-estimate accuracy (RMSE, MAE), conventional PHM architectures implicitly assume that input telemetry is authentic and model artifacts are uncorrupted.

In distributed aviation maintenance architectures, ground-side predictive maintenance analytics receive telemetry dispatched over commercial ground data links or offloaded via post-flight data terminals. These data interfaces introduce realistic attack vectors:
1. **Model-Artifact Tampering / Supply-Chain Compromise:** Substitution of regressor weights, feature scaler parameters, or manifest metadata in offline model stores or edge caches.
2. **Sensor Telemetry Manipulation:** Intentional spoofing, bias injection, calibration drift, or freeze-replay attacks against high-sensitivity degradation channels (e.g., $s_{11}$ static HPC pressure, $s_4$ LPC exit temperature).

The primary research problem is formulated as:
> *How effectively can lightweight integrity controls (asymmetric cryptographic authentication and statistical drift detectors) detect manipulated sensor inputs and model-artifact tampering in an aircraft predictive-maintenance pipeline, and how much harmful change in remaining-useful-life predictions can remain undetected?*

---

## 2. Formal Research Questions (RQs)

* **RQ1 (Artifact Integrity & Authentication):**  
  *Can asymmetric cryptographic signing (Ed25519) combined with deterministic canonical JSON serialization authenticate ML model pipelines with sub-millisecond overhead and fail-closed security against arbitrary byte corruption, metadata alteration, or untrusted public keys?*

* **RQ2 (Sensor Telemetry Evasion & Drift Blind Spots):**  
  *To what extent can subtle sensor manipulations (single-channel bias shifts $\le \pm 2\sigma$, gradual creeping ramps, or frozen replays) bypass standard operational drift controls (Kolmogorov-Smirnov two-sample tests and Population Stability Index) while inducing severe RUL prediction degradation?*

* **RQ3 (Asymmetric Risk & Hazardous Prediction Rate):**  
  *What is the impact of evasive telemetry attacks on late-stage maintenance decisions, specifically quantified by the Hazardous Prediction Rate (HPR, over-predicting RUL $>25$ cycles when true RUL $\le 25$) and the NASA asymmetric exponential penalty function?*

* **RQ4 (Operational Feasibility & Resource Footprint):**  
  *What is the empirical computational latency cost of enforcing end-to-end integrity controls (cryptographic verification, input schema hardening, dual-baseline drift screening) relative to standard unverified ML inference?*

---

## 3. Threat Model & Trust Boundaries

### 3.1 Assets Under Protection
1. **Trained Estimator Artifacts:** `model.joblib` (HistGradientBoostingRegressor, 2.76 MB).
2. **Feature Engineering Preprocessors:** `preprocessor.joblib` (RobustScaler + PolynomialFeatures, 16.7 MB).
3. **Model Lineage Manifest:** `model_manifest.json` (canonical JSON metadata defining dataset SHA-256, protocol metrics, timestamp, and signature).
4. **Input Telemetry Streams:** 14 active degradation sensor channels across operating cycles $t \in [1, T]$.
5. **Inference Outputs:** RUL point estimates, risk band categorizations, and maintenance scheduling advisories.

### 3.2 Attacker Capabilities & Access Profiles
* **Adversary $\mathcal{A}_{\text{art}}$ (Supply-Chain / Artifact Tamperer):**  
  Has read/write access to model storage or local file systems. Attempts to modify model weights, scaling parameters, or manifest records. $\mathcal{A}_{\text{art}}$ does NOT possess the offline Ed25519 private signing key ($sk_{\text{ed25519}}$).
* **Adversary $\mathcal{A}_{\text{sen}}$ (Telemetry Manipulator):**  
  Man-in-the-Middle (MitM) or compromised ground telematics receiver. Can inject additive biases ($\delta \in [-2\sigma, +2\sigma]$), creeping linear drift ($\alpha \cdot t$), or frozen sensor buffers into unauthenticated telemetry channels. Does NOT possess access to ground-truth labels $y^*$.

### 3.3 Security Invariants
* **Invariant 1 (Fail-Closed Deserialization):** Under unauthenticated or modified bytes, the application MUST reject deserialization and abort pipeline initialization.
* **Invariant 2 (Dual Protocol Separation):** Evaluation results under unclipped ground-truth (Protocol A) and clipped ground-truth ($RUL_{\max}=125$, Protocol B) must never be conflated.
* **Invariant 3 (Offline Evaluation Quarantine):** True ground-truth RUL $y^*$ must never be provided as an input feature or used in online drift screening.

---

## 4. Key Hypotheses

* **$H_1$ (Cryptographic Defense):** Ed25519 verification achieves 100% true-negative rejection of altered artifacts with latency cost $< 1.0\text{ ms}$, rendering offline artifact tampering completely unviable without private key compromise.
* **$H_2$ (Drift Detector Evasion):** Multi-channel drift detectors calibrated at the fleet level will experience significant blind spots: single-channel bias injections within $\pm 2\sigma$ of sensor variance will trigger $\le 1$ PSI alert channel, evading fleet-level drift thresholds while shifting RUL estimates by $>9$ cycles.
* **$H_3$ (Hazardous Over-Prediction):** Negative sensor biases on high-importance degradation sensors ($s_{11}$, static HPC pressure) delay predicted engine retirement, elevating the Hazardous Prediction Rate (HPR) by over $15\%$ and increasing NASA asymmetric risk exponentially.
* **$H_4$ (Censoring Asymmetry in Baselines):** Comparing operational test telemetry (where engines are stopped at arbitrary pre-failure cycles) directly against training baselines (where all engines run to complete structural failure) creates massive false-positive drift alarms ($\ge 8$ channels), necessitating an operational test-derived drift baseline.
